"""Verifier sub-agent: groundedness check in an isolated context."""
from __future__ import annotations

from google.genai import types
from pydantic import BaseModel, Field

from .. import config
from .gemini_util import generate_with_retry
from .tokens import TokenLedger

VERIFIER_SYSTEM = (
    "You are a strict grounding verifier for a course assistant. "
    "You receive ONLY: the user question, a proposed answer, and a compact "
    "evidence notebook. You do not search. Decide whether every factual claim "
    "in the answer is supported by the notebook. "
    "If the answer correctly escalates because evidence is missing, that is a PASS. "
    "If the answer invents course facts not in the notebook, FAIL."
)


class VerificationResult(BaseModel):
    passed: bool = Field(description="True if the answer is adequately grounded.")
    issues: str = Field(
        default="",
        description="If failed, list unsupported claims or missing evidence.",
    )


def run_verifier(
    client,
    *,
    question: str,
    proposed_answer: str,
    escalate: bool,
    evidence_digest: str,
    ledger: TokenLedger,
    temperature: float = 0.0,
) -> VerificationResult:
    prompt = (
        f"User question:\n{question}\n\n"
        f"Proposed answer:\n{proposed_answer}\n\n"
        f"escalate_to_human={escalate}\n\n"
        f"{evidence_digest}\n\n"
        "Return JSON: passed + issues."
    )
    response = generate_with_retry(
        client,
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=VERIFIER_SYSTEM,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=VerificationResult,
        ),
    )
    ledger.record(response, agent="verifier")
    parsed = response.parsed
    if parsed is None:
        return VerificationResult(passed=False, issues="Verifier returned no parseable result.")
    return parsed
