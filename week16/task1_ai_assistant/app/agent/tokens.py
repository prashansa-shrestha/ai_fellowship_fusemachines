"""Token / usage accounting helpers for Gemini responses."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenLedger:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    by_agent: dict[str, int] = field(default_factory=dict)

    def record(self, response, agent: str = "unknown") -> None:
        self.calls += 1
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return
        prompt = int(getattr(usage, "prompt_token_count", 0) or 0)
        completion = int(getattr(usage, "candidates_token_count", 0) or 0)
        total = int(getattr(usage, "total_token_count", 0) or (prompt + completion))
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total
        self.by_agent[agent] = self.by_agent.get(agent, 0) + total

    def as_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.calls,
            "by_agent": dict(self.by_agent),
        }
