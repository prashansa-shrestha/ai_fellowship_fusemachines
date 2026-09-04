from typing import List

from pydantic import BaseModel, Field


class AssistantAnswer(BaseModel):
    """JSON shape the model must emit for the final Gemini pass."""

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


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    escalate_to_human: bool = False
    provider_used: str
