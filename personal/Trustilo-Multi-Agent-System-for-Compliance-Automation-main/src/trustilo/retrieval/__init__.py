"""Tenant-filtered hybrid retrieval + re-ranking (FR4).

See specs/05-retrieval.md and this package's AGENTS.md.
SECURITY-SENSITIVE: read specs/12-security-and-governance.md before
writing any query here.
"""

from trustilo.retrieval.search import InMemoryEvidenceIndex


__all__ = ["InMemoryEvidenceIndex"]
