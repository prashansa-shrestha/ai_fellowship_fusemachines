import os
from pathlib import Path

from dotenv import load_dotenv

from .net import force_ipv4_dns

load_dotenv()
force_ipv4_dns()

_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = _ROOT / "data" / "corpus"
INDEX_DIR = _ROOT / "data" / "index"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("TOP_K", "4"))

DEFAULT_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))
DEFAULT_TOP_P = float(os.getenv("GEMINI_TOP_P", "0.9"))

# W16 agentic loop knobs
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "8"))
AGENT_MAX_VERIFY_FAILURES = int(os.getenv("AGENT_MAX_VERIFY_FAILURES", "2"))
NOTEBOOK_MAX_ENTRIES = int(os.getenv("NOTEBOOK_MAX_ENTRIES", "8"))
NOTEBOOK_EXCERPT_CHARS = int(os.getenv("NOTEBOOK_EXCERPT_CHARS", "220"))
# Default chat path: agentic multi-agent loop (set "legacy" for W15 two-phase path)
DEFAULT_CHAT_MODE = os.getenv("DEFAULT_CHAT_MODE", "agent")
