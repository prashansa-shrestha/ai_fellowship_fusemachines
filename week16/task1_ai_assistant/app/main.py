"""Course assistant API — POST /chat, GET /health.

W16 default: explicit researcher + verifier agentic loop.
Legacy W15 path still available via mode=legacy.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import config
from .agent import run_agentic_chat
from .llm_client import GeminiClient, OllamaClient
from .rag import RagIndex
from .schemas import ChatRequest, ChatResponse
from .tools import make_tools

_runtime: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    index = RagIndex()
    faiss_path = config.INDEX_DIR / "index.faiss"
    if faiss_path.exists():
        index.load(config.INDEX_DIR)
    else:
        index.build(config.CORPUS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        index.save(config.INDEX_DIR)

    _runtime["rag"] = index
    _runtime["gemini"] = GeminiClient()
    _runtime["ollama"] = OllamaClient()
    try:
        yield
    finally:
        _runtime.clear()


app = FastAPI(title="Fusemachines Course Assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "chunks_indexed": len(_runtime["rag"].chunks)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    temp = config.DEFAULT_TEMPERATURE if req.temperature is None else req.temperature
    top_p = config.DEFAULT_TOP_P if req.top_p is None else req.top_p
    mode = (req.mode or config.DEFAULT_CHAT_MODE).lower()

    if req.provider == "ollama":
        try:
            reply = _runtime["ollama"].chat(req.message, temp)
        except Exception as err:
            raise HTTPException(status_code=502, detail=f"Local model unavailable: {err}")
        return ChatResponse(
            answer=reply,
            sources=[],
            escalate_to_human=False,
            provider_used="ollama",
            mode_used="ollama",
        )

    # --- W16 agentic path (default) ---
    if mode == "agent":
        try:
            result = run_agentic_chat(
                _runtime["rag"],
                req.message,
                temperature=temp,
                top_p=top_p,
                inject_failure=req.inject_failure,
                single_agent=req.single_agent,
            )
        except Exception as err:
            raise HTTPException(status_code=502, detail=f"Agent request failed: {err}")

        return ChatResponse(
            answer=result.answer,
            sources=result.sources,
            escalate_to_human=result.escalate_to_human,
            provider_used=result.provider_used,
            iterations=result.iterations,
            stopped_reason=result.stopped_reason,
            tokens=result.tokens,
            tool_log=result.tool_log,
            trace=[
                {
                    "iteration": s.iteration,
                    "agent": s.agent,
                    "action": s.action,
                    "detail": s.detail,
                }
                for s in result.trace
            ],
            mode_used=result.mode,
            clarification=result.clarification,
        )

    # --- W15 legacy two-phase Gemini path ---
    tracked_sources: list[str] = []
    tool_fns = make_tools(_runtime["rag"], tracked_sources)
    try:
        parsed = _runtime["gemini"].chat(req.message, tool_fns, temp, top_p)
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {err}")

    return ChatResponse(
        answer=parsed.answer,
        sources=tracked_sources or parsed.sources,
        escalate_to_human=parsed.escalate_to_human,
        provider_used="gemini",
        mode_used="legacy",
    )
