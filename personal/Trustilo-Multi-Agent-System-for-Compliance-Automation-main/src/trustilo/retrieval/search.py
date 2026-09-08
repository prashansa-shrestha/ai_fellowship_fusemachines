"""Tenant-isolated, deterministic lexical retrieval for the local demo.

The production design uses tenant-filtered PostgreSQL queries.  This small
in-memory equivalent preserves the important security ordering: select one
tenant bucket first, then filter versions and rank only that bucket.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from types import MappingProxyType

from trustilo.common.schemas import EvidenceChunk, Question


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_QUESTION_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "can",
        "describe",
        "did",
        "do",
        "does",
        "for",
        "how",
        "is",
        "of",
        "the",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "you",
        "your",
    }
)


def _tokens(text: str) -> tuple[str, ...]:
    """Return stable, case-insensitive word tokens without punctuation."""

    return tuple(_TOKEN_RE.findall(text.casefold()))


def _query_tokens(text: str) -> tuple[str, ...]:
    """Prefer content words, but retain all words for stop-word-only queries."""

    tokens = _tokens(text)
    content_tokens = tuple(token for token in tokens if token not in _QUESTION_STOP_WORDS)
    return content_tokens or tokens


def _aware_utc(value: datetime, *, label: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _is_active(chunk: EvidenceChunk, as_of: datetime) -> bool:
    """Return whether ``chunk`` is valid at ``as_of`` (inclusive bounds)."""

    valid_from = chunk.version_info.valid_from
    if valid_from is not None and as_of < _aware_utc(
        valid_from, label=f"valid_from for chunk {chunk.chunk_id!r}"
    ):
        return False

    valid_until = chunk.version_info.valid_until
    if valid_until is not None and as_of > _aware_utc(
        valid_until, label=f"valid_until for chunk {chunk.chunk_id!r}"
    ):
        return False

    return True


def _rank_key(chunk: EvidenceChunk, query_tokens: tuple[str, ...]) -> tuple[object, ...] | None:
    """Build an ascending sort key, or ``None`` for an irrelevant chunk."""

    chunk_tokens = _tokens(chunk.text)
    query_counts = Counter(query_tokens)
    chunk_counts = Counter(chunk_tokens)
    overlap_count = sum(
        min(count, chunk_counts[token]) for token, count in query_counts.items()
    )
    if overlap_count == 0:
        return None

    covered_terms = len(query_counts.keys() & chunk_counts.keys())
    coverage = covered_terms / len(query_counts)
    query_phrase = " ".join(query_tokens)
    exact_phrase = query_phrase in " ".join(chunk_tokens)

    # Negative score components make Python's ascending sort put stronger
    # matches first.  IDs and provenance provide stable, input-order-free ties.
    return (
        -int(exact_phrase),
        -coverage,
        -overlap_count,
        chunk.chunk_id,
        chunk.doc_id,
        chunk.version_info.version,
        chunk.version_info.source,
        chunk.text,
    )


class InMemoryEvidenceIndex:
    """A defensive, read-only snapshot of evidence grouped by tenant.

    Source chunks are deep-copied into tenant buckets at construction, and
    search results are deep-copied again.  Mutating the caller's input or a
    returned result therefore cannot alter the index or move evidence between
    tenant scopes.
    """

    __slots__ = ("_chunks_by_tenant",)

    def __init__(self, chunks: Iterable[EvidenceChunk]) -> None:
        buckets: dict[str, list[EvidenceChunk]] = defaultdict(list)
        for chunk in chunks:
            if not isinstance(chunk, EvidenceChunk):
                raise TypeError("InMemoryEvidenceIndex accepts only EvidenceChunk objects")
            snapshot = chunk.model_copy(deep=True)
            buckets[snapshot.tenant_id].append(snapshot)

        immutable_buckets = {
            tenant_id: tuple(tenant_chunks)
            for tenant_id, tenant_chunks in buckets.items()
        }
        self._chunks_by_tenant: Mapping[str, tuple[EvidenceChunk, ...]] = MappingProxyType(
            immutable_buckets
        )

    def search(
        self,
        question: Question,
        tenant_id: str,
        top_k: int,
        revised_query: str | None = None,
        *,
        as_of: datetime | None = None,
    ) -> list[EvidenceChunk]:
        """Return active, relevant evidence from exactly one tenant bucket.

        ``revised_query`` replaces (rather than augments) the question text.
        Version bounds are inclusive.  When ``as_of`` is omitted, the current
        UTC time is used; callers and tests may inject it for repeatability.
        """

        if not isinstance(question, Question):
            raise TypeError("question must be a Question")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-blank string")
        if question.tenant_id != tenant_id:
            raise ValueError("question.tenant_id must match tenant_id")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if revised_query is not None and (
            not isinstance(revised_query, str) or not revised_query.strip()
        ):
            raise ValueError("revised_query must be a non-blank string when provided")

        query_text = (
            revised_query
            if revised_query is not None
            else question.normalized_text or question.raw_text
        )
        query_tokens = _query_tokens(query_text)
        if not query_tokens:
            raise ValueError("question text must contain at least one word")

        effective_as_of = _aware_utc(
            as_of if as_of is not None else datetime.now(timezone.utc),
            label="as_of",
        )

        # SECURITY (NFR2): choose one tenant bucket before version checks or
        # scoring.  No global candidate list exists in this search path.
        tenant_chunks = self._chunks_by_tenant.get(tenant_id, ())
        ranked: list[tuple[tuple[object, ...], EvidenceChunk]] = []
        for chunk in tenant_chunks:
            if not _is_active(chunk, effective_as_of):
                continue
            rank_key = _rank_key(chunk, query_tokens)
            if rank_key is not None:
                ranked.append((rank_key, chunk))

        ranked.sort(key=lambda item: item[0])
        return [chunk.model_copy(deep=True) for _, chunk in ranked[:top_k]]
