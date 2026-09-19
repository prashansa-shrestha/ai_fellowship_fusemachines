"""AG_NEWS topic router API with cache, rate limits, and Gemini fallback."""
import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import config
from .cache import TTLCache
from .fallback import GeminiFallbackClassifier
from .model import RouterModel
from .schemas import PredictBatchRequest, PredictRequest, PredictResponse

_ctx: dict = {}
_pool = ThreadPoolExecutor(max_workers=4)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ctx["model"] = RouterModel()
    _ctx["fallback"] = GeminiFallbackClassifier()
    _ctx["cache"] = TTLCache(config.CACHE_MAX_SIZE, config.CACHE_TTL_SECONDS)
    try:
        yield
    finally:
        _ctx.clear()


app = FastAPI(title="AG_NEWS Topic Router", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def _classify_with_fallback(text: str) -> tuple[dict, str]:
    """ONNX first; Gemini on failure; UNKNOWN if both fail. Runs in the pool."""
    try:
        return _ctx["model"].predict_one(text), "onnx_local"
    except Exception:
        pass

    try:
        return _ctx["fallback"].predict_one(text), "gemini_fallback"
    except Exception:
        return (
            {"category": "UNKNOWN", "confidence": 0.0, "probabilities": None},
            "degraded",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
@limiter.limit(config.RATE_LIMIT)
async def predict(request: Request, body: PredictRequest):
    t0 = time.time()
    key = _cache_key(body.text)

    hit = _ctx["cache"].get(key)
    if hit is not None:
        return PredictResponse(**hit, cached=True, latency_ms=(time.time() - t0) * 1000)

    loop = asyncio.get_running_loop()
    result, provider = await loop.run_in_executor(_pool, _classify_with_fallback, body.text)

    payload = {**result, "provider_used": provider}
    _ctx["cache"].set(key, payload)
    return PredictResponse(**payload, cached=False, latency_ms=(time.time() - t0) * 1000)


@app.post("/predict_batch", response_model=list[PredictResponse])
@limiter.limit(config.RATE_LIMIT)
async def predict_batch(request: Request, body: PredictBatchRequest):
    t0 = time.time()
    loop = asyncio.get_running_loop()

    try:
        rows = await loop.run_in_executor(_pool, _ctx["model"].predict_batch, body.texts)
        provider = "onnx_local"
    except Exception:
        # No batch Gemini API — walk items through the single-item path.
        rows = []
        providers = []
        for text in body.texts:
            row, provider = _classify_with_fallback(text)
            rows.append(row)
            providers.append(provider)
        elapsed = (time.time() - t0) * 1000
        return [
            PredictResponse(**row, provider_used=p, cached=False, latency_ms=elapsed)
            for row, p in zip(rows, providers)
        ]

    elapsed = (time.time() - t0) * 1000
    return [
        PredictResponse(**row, provider_used=provider, cached=False, latency_ms=elapsed)
        for row in rows
    ]
