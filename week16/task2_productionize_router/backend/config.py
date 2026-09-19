import os
from pathlib import Path

from dotenv import load_dotenv

from .net import force_ipv4_dns

load_dotenv()
force_ipv4_dns()

_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = _ROOT / "artifacts"

ONNX_MODEL_PATH = ARTIFACTS_DIR / "model.quant.onnx"
VOCAB_PATH = ARTIFACTS_DIR / "vocab.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

RATE_LIMIT = os.getenv("RATE_LIMIT", "30/minute")
