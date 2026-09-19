"""Researcher tools for the explicit agentic loop (manual function calling)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from .. import config
from ..rag import RagIndex
from .notes import EvidenceNotebook

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _skill_catalog() -> str:
    summary = (SKILLS_DIR / "SKILL.md").read_text(encoding="utf-8")
    return summary.strip()


def make_researcher_tools(
    rag: RagIndex,
    notebook: EvidenceNotebook,
    *,
    inject_failure: str | None = None,
) -> tuple[list[Callable[..., Any]], dict[str, Any]]:
    """Return (python callables for Gemini tools, shared mutable state)."""

    state: dict[str, Any] = {
        "proposed": None,  # dict with answer/sources/escalate
        "clarification": None,
        "skill_loaded": False,
        "tool_log": [],  # list of {name, args, ok}
        "inject_failure": inject_failure,
    }

    def search_course_materials(query: str) -> str:
        """Search course materials. Results are capped and stored in the evidence notebook;
        only a short digest is returned so prior raw dumps do not accumulate.

        Args:
            query: Short search query about course content.
        """
        if state["inject_failure"] == "tool_unavailable":
            state["tool_log"].append(
                {"name": "search_course_materials", "args": {"query": query}, "ok": False}
            )
            return (
                "ERROR: search_course_materials is temporarily unavailable "
                "(injected failure). Do not invent course content. "
                "Ask for clarification or propose_answer with escalate_to_human=true."
            )

        hits = rag.search(query, top_k=config.TOP_K)

        if state["inject_failure"] == "malformed_retrieval":
            state["tool_log"].append(
                {"name": "search_course_materials", "args": {"query": query}, "ok": False}
            )
            # Intentionally broken payload — agent should not treat as evidence.
            return "{{not-json::: garbage<<< retrieval failed"

        digest = notebook.add_hits(query, hits)
        state["tool_log"].append(
            {"name": "search_course_materials", "args": {"query": query}, "ok": True}
        )
        return digest

    def list_available_weeks() -> str:
        """List which week numbers exist in the indexed corpus."""
        found: set[int] = set()
        for hit in rag.chunks:
            m = re.match(r"Week_(\d+)_", hit.source)
            if m:
                found.add(int(m.group(1)))
        state["tool_log"].append({"name": "list_available_weeks", "args": {}, "ok": True})
        return "Available weeks: " + ", ".join(str(w) for w in sorted(found))

    def load_skill(skill_name: str) -> str:
        """Load full skill instructions when the catalog summary is not enough.

        Args:
            skill_name: Skill id, e.g. compare_course_options.
        """
        path = SKILLS_DIR / f"{skill_name}.md"
        if not path.exists():
            state["tool_log"].append(
                {"name": "load_skill", "args": {"skill_name": skill_name}, "ok": False}
            )
            return f"Unknown skill {skill_name!r}. Catalog:\n{_skill_catalog()}"
        state["skill_loaded"] = True
        state["tool_log"].append(
            {"name": "load_skill", "args": {"skill_name": skill_name}, "ok": True}
        )
        return path.read_text(encoding="utf-8")

    def ask_clarification(question: str) -> str:
        """Stop and ask the user a clarifying question when evidence is insufficient.

        Args:
            question: One clear question for the user.
        """
        state["clarification"] = question
        state["tool_log"].append(
            {"name": "ask_clarification", "args": {"question": question}, "ok": True}
        )
        return "Clarification will be returned to the user. Stop searching."

    def propose_answer(answer: str, escalate_to_human: bool = False) -> str:
        """Propose a final answer for the verifier. Call only when ready.

        Args:
            answer: Plain-language answer grounded in the evidence notebook.
            escalate_to_human: True if materials do not cover the question.
        """
        state["proposed"] = {
            "answer": answer,
            "sources": notebook.sources(),
            "escalate_to_human": bool(escalate_to_human),
        }
        state["tool_log"].append(
            {
                "name": "propose_answer",
                "args": {"escalate_to_human": bool(escalate_to_human)},
                "ok": True,
            }
        )
        return "Proposal recorded. A verifier will check grounding next."

    tools = [
        search_course_materials,
        list_available_weeks,
        load_skill,
        ask_clarification,
        propose_answer,
    ]
    state["skill_catalog"] = _skill_catalog()
    return tools, state
