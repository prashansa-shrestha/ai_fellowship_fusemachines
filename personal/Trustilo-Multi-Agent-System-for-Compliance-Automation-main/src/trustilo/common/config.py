"""Minimal settings loader, matching `.env.example` at the repo root.

Kept deliberately small (stdlib `os.environ` + `python-dotenv`) rather
than pulling in a settings framework — extend this if/when the team
actually needs more than a handful of values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    anthropic_api_key: str | None
    openai_api_key: str | None
    object_store_endpoint: str
    object_store_bucket: str
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process. Call `get_settings.cache_clear()`
    in tests if you need to reload after changing environment
    variables mid-run."""
    load_dotenv()
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql+asyncpg://trustilo:trustilo@localhost:5432/trustilo"
        ),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
        object_store_endpoint=os.environ.get("OBJECT_STORE_ENDPOINT", "http://localhost:9000"),
        object_store_bucket=os.environ.get("OBJECT_STORE_BUCKET", "trustilo-evidence"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
