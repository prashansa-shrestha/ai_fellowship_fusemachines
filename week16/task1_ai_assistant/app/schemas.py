from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssistantAnswer(BaseModel):
    """JSON shape the model must emit for the final Gemini pass (legacy path)."""

    answer: str = Field(description="Plain-language answer to the user.")
    sources: List[str] = Field(default_factory=list, description="Course material filenames used.")
    escalate_to_human: bool = Field(
        default=False,
        description="Set true when course materials don't cover the question.",
    )


class ChatRequest(BaseModel):
    message: str
    temperature: float | None = None
    top_p: float | None = None
    provider: str = "gemini"  # gemini | ollama
    # agent = W16 researcher+verifier loop; legacy = W15 two-phase auto tools
    mode: str | None = None
    # Eval / demo only: tool_unavailable | malformed_retrieval
    inject_failure: str | None = None
    # If true, skip verifier (single-agent baseline for token comparison)
    single_agent: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    escalate_to_human: bool = False
    provider_used: str
    # W16 agent metadata (empty/defaults on legacy + ollama paths)
    iterations: int = 0
    stopped_reason: str = ""
    tokens: Dict[str, Any] = Field(default_factory=dict)
    tool_log: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    mode_used: str = ""
    clarification: Optional[str] = None
