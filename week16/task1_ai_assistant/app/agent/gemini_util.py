"""Shared Gemini call helpers."""
from __future__ import annotations

import time

from google.genai.errors import APIError, ClientError, ServerError


def generate_with_retry(client, **kwargs):
    """Retry Gemini calls on free-tier 429 / transient 503."""
    last_err: Exception | None = None
    for attempt in range(8):
        try:
            return client.models.generate_content(**kwargs)
        except (ClientError, ServerError, APIError) as err:
            last_err = err
            msg = str(err)
            retryable = (
                "429" in msg
                or "RESOURCE_EXHAUSTED" in msg
                or "503" in msg
                or "UNAVAILABLE" in msg
                or "high demand" in msg.lower()
            )
            if not retryable:
                raise
            delay = 20.0 * (attempt + 1)
            if "Please retry in" in msg:
                try:
                    delay = float(msg.split("Please retry in")[1].split("s")[0].strip()) + 1.0
                except (IndexError, ValueError):
                    pass
            print(f"[gemini retry {attempt + 1}] waiting {delay:.0f}s: {msg[:100]}", flush=True)
            time.sleep(min(delay, 120.0))
    assert last_err is not None
    raise last_err
