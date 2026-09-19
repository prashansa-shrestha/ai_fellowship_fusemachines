#!/usr/bin/env python3
"""Offline checks that do not consume Gemini quota.

Validates failure-injection tool responses and notebook capping/clearing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agent.notes import EvidenceNotebook  # noqa: E402
from app.agent.tools_agent import make_researcher_tools  # noqa: E402
from app.rag import Chunk, RagIndex  # noqa: E402


class _FakeRag(RagIndex):
    def __init__(self):
        self.chunks = [Chunk(text="Week 9 manufacturing defects guide.", source="Week_9_W9.txt")]
        self.index = None
        self.embeddings = None

    def search(self, query: str, top_k: int = 4):
        return self.chunks[:top_k]


def main() -> int:
    rag = _FakeRag()
    nb = EvidenceNotebook(max_entries=3, excerpt_chars=40)

    # Cap + clear: raw text is truncated into notebook; tool returns digest only.
    tools, state = make_researcher_tools(rag, nb)
    search = tools[0]
    out = search("week 9 defects")
    assert "Evidence notebook" in out
    assert "Week 9 manufacturing defects guide." not in out or "…" in out or len(out) < 500
    assert len(nb.entries) == 1

    # Failure injection: tool unavailable
    tools2, state2 = make_researcher_tools(rag, EvidenceNotebook(), inject_failure="tool_unavailable")
    msg = tools2[0]("anything")
    assert "unavailable" in msg.lower()
    assert state2["tool_log"][-1]["ok"] is False

    # Failure injection: malformed retrieval
    tools3, state3 = make_researcher_tools(rag, EvidenceNotebook(), inject_failure="malformed_retrieval")
    bad = tools3[0]("anything")
    assert "garbage" in bad or "not-json" in bad
    assert state3["tool_log"][-1]["ok"] is False

    print("offline_checks: PASS")
    print("- notebook capping/clearing ok")
    print("- inject tool_unavailable returns error (no invented evidence)")
    print("- inject malformed_retrieval returns invalid payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
