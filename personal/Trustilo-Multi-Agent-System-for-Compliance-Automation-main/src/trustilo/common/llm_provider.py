"""Provider-agnostic LLM client interface (NFR7).

No pipeline stage imports `anthropic`, `openai`, or any other vendor
SDK directly — it calls `get_provider(model_id)` from here instead.
That's what makes "no hard dependency on one LLM vendor" (NFR7) true
in code, not just in a design doc, and it's what lets
`ExperimentConfig.model_ids` (see `schemas.py`) actually control which
model powers which stage per experiment.

This module defines the interface and a small registry; it
deliberately does not hardcode a default vendor or model — every
model choice should be explicit in an `ExperimentConfig`, per
`specs/03-orchestrator.md`'s config-stamping requirement. Wire up
concrete provider classes (e.g. one wrapping the `anthropic` SDK, one
wrapping `openai`) as the project needs them; this file stays the only
place those imports live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_id: str


@runtime_checkable
class LLMProvider(Protocol):
    """What pipeline stages actually depend on — never a vendor SDK directly."""

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any] | None = None,
        max_tokens: int = 1024,
    ) -> CompletionResult:
        """Run one completion.

        `response_schema`, if given, requests structured output
        matching that JSON schema. Drafting and verification should
        always pass a schema — see
        `.cursor/rules/llm-prompting-and-grounding.mdc` — never parse
        citations or claims out of free text.
        """
        ...


_PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {}


def register_provider(model_id_prefix: str, provider_cls: type[LLMProvider]) -> None:
    """Register a concrete provider for model_ids starting with `model_id_prefix`.

    Call this once at process startup for each vendor integration you
    add, e.g. `register_provider("claude-", AnthropicProvider)`.
    """
    _PROVIDER_REGISTRY[model_id_prefix] = provider_cls


def get_provider(model_id: str) -> LLMProvider:
    """Resolve a model_id (from `ExperimentConfig.model_ids`) to a provider instance.

    Raises if nothing matches — fails loudly rather than silently
    falling back to some default vendor, since every model choice
    should be an explicit, config-stamped decision (NFR7).
    """
    for prefix, provider_cls in _PROVIDER_REGISTRY.items():
        if model_id.startswith(prefix):
            return provider_cls()  # type: ignore[call-arg]
    raise ValueError(
        f"No LLM provider registered for model_id={model_id!r}. "
        "Register a concrete implementation with register_provider() "
        "before using this model_id — see this module's docstring."
    )
