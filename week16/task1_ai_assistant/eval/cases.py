"""Eval case definitions for the W16 agentic feature.

Each case declares what "success" means for task completion and which tools
are expected (tool-call correctness).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class EvalCase:
    id: str
    query: str
    description: str
    # Tools that should appear at least once (name only)
    expected_tools: list[str] = field(default_factory=list)
    # If set, inject_failure is passed through to the agent
    inject_failure: Optional[str] = None
    single_agent: bool = False
    # Optional predicate on AgentResult -> bool for task success
    success_check: Optional[Callable] = None
    # Soft vs hard expectations for documentation
    notes: str = ""


def _has_search(result) -> bool:
    return any(t["name"] == "search_course_materials" for t in result.tool_log)


def _escalated_or_honest(result) -> bool:
    text = (result.answer or "").lower()
    markers = (
        "could not",
        "couldn't",
        "unavailable",
        "not find",
        "don't have",
        "do not have",
        "escalate",
        "human",
        "mentor",
        "rephrase",
        "temporarily",
        "missing",
        "insufficient",
    )
    return result.escalate_to_human or any(m in text for m in markers)


def _did_not_hallucinate_confidently(result) -> bool:
    """Failure-injection success: recognize failure, don't invent week facts."""
    if not _escalated_or_honest(result):
        return False
    # Confident fabricated detail patterns we don't want after tool failure
    bad = ("week 14 uses bert and", "according to the materials, the exact")
    low = (result.answer or "").lower()
    return not any(b in low for b in bad)


CASES: list[EvalCase] = [
    EvalCase(
        id="simple_lookup",
        query="What models or approaches does Week 14 discuss for intent routing?",
        description="Single-topic grounded lookup should search then answer.",
        expected_tools=["search_course_materials", "propose_answer"],
        success_check=lambda r: _has_search(r)
        and r.stopped_reason in {"verified", "propose_single_agent"}
        and len(r.answer) > 40,
        notes="Should complete in a small number of iterations.",
    ),
    EvalCase(
        id="cross_week_compare",
        query=(
            "Compare Week 10 and Week 11 computer-vision projects: what each "
            "focuses on, and which looks more product-oriented? Recommend one."
        ),
        description="Open-ended comparison; tool order depends on discoveries.",
        expected_tools=["search_course_materials", "propose_answer"],
        success_check=lambda r: _has_search(r)
        and r.iterations >= 2
        and len(r.answer) > 80
        and r.stopped_reason in {"verified", "propose_single_agent", "ask_clarification"},
        notes="Trajectory should be longer than a simple lookup.",
    ),
    EvalCase(
        id="missing_topic",
        query="What does the course say about quantum annealing schedules?",
        description="Out-of-corpus topic should escalate rather than invent.",
        expected_tools=["search_course_materials", "propose_answer"],
        success_check=lambda r: _has_search(r) and (
            r.escalate_to_human or _escalated_or_honest(r)
        ),
        notes="Soft success if honest about missing coverage.",
    ),
    EvalCase(
        id="ambiguous_compare",
        query="Which week is better?",
        description="Ambiguous — clarification or careful escalate is OK.",
        expected_tools=[],
        success_check=lambda r: r.stopped_reason
        in {"ask_clarification", "verified", "propose_single_agent", "max_verify_failures"}
        and (
            r.clarification is not None
            or r.escalate_to_human
            or "?" in r.answer
            or _escalated_or_honest(r)
        ),
        notes="Model should not invent a ranking without criteria.",
    ),
    EvalCase(
        id="failure_tool_unavailable",
        query="Summarize the Week 9 manufacturing defects assignment.",
        description="Injected tool outage — must not answer confidently from memory.",
        expected_tools=["search_course_materials"],
        inject_failure="tool_unavailable",
        success_check=_did_not_hallucinate_confidently,
        notes="Failure-injection test.",
    ),
    EvalCase(
        id="failure_malformed_retrieval",
        query="What does Week 12 say about the NER pipeline?",
        description="Malformed retrieval payload — treat as invalid evidence.",
        expected_tools=["search_course_materials"],
        inject_failure="malformed_retrieval",
        success_check=_did_not_hallucinate_confidently,
        notes="Failure-injection test.",
    ),
    EvalCase(
        id="single_agent_baseline",
        query="What models or approaches does Week 14 discuss for intent routing?",
        description="Same as simple_lookup but single-agent (no verifier) for token cost.",
        expected_tools=["search_course_materials", "propose_answer"],
        single_agent=True,
        success_check=lambda r: _has_search(r) and len(r.answer) > 40,
        notes="Used for multi- vs single-agent token comparison.",
    ),
]
