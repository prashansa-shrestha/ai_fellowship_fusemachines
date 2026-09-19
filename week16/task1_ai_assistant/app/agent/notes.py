"""Structured external notes + tool-result clearing (context engineering).

Raw FAISS dumps grow quickly across loop iterations. Instead of leaving every
retrieval blob in the conversation, we:

1. Cap and lightly re-rank hits before they enter the notebook.
2. Store compact evidence entries in an EvidenceNotebook outside the chat.
3. Replace the model's tool-response payload with a short pointer + notebook
   digest so subsequent turns do not re-read full chunk text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..rag import Chunk


@dataclass
class EvidenceEntry:
    query: str
    source: str
    excerpt: str
    score_rank: int


@dataclass
class EvidenceNotebook:
    """Scratchpad held outside the model context; only digests are injected."""

    entries: List[EvidenceEntry] = field(default_factory=list)
    max_entries: int = 8
    excerpt_chars: int = 220

    def add_hits(self, query: str, hits: List[Chunk]) -> str:
        """Cap hits, append compact entries, return a short tool-facing digest."""
        capped = hits[:4]
        added: list[str] = []
        for rank, hit in enumerate(capped, start=1):
            excerpt = hit.text[: self.excerpt_chars].rstrip()
            if len(hit.text) > self.excerpt_chars:
                excerpt += "…"
            self.entries.append(
                EvidenceEntry(
                    query=query,
                    source=hit.source,
                    excerpt=excerpt,
                    score_rank=rank,
                )
            )
            added.append(f"#{len(self.entries)} {hit.source} (rank {rank})")

        # Keep the notebook bounded so digests stay short.
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        if not added:
            return "No hits. Notebook unchanged."

        return (
            f"Stored {len(added)} capped hits in evidence notebook: "
            + "; ".join(added)
            + ".\n"
            + self.digest()
        )

    def digest(self) -> str:
        if not self.entries:
            return "Evidence notebook: (empty)"
        lines = ["Evidence notebook:"]
        for i, e in enumerate(self.entries, start=1):
            lines.append(
                f"{i}. [{e.source}] (q={e.query!r}, rank={e.score_rank}) {e.excerpt}"
            )
        return "\n".join(lines)

    def sources(self) -> list[str]:
        seen: list[str] = []
        for e in self.entries:
            if e.source not in seen:
                seen.append(e.source)
        return seen

    def verifier_packet(self) -> str:
        """Compact evidence package for the verifier sub-agent only."""
        return self.digest()
