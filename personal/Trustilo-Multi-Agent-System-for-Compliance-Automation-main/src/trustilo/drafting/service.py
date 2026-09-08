"""Deterministic, citation-safe drafting for the local Phase 3 demo."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from trustilo.common.schemas import (
    Answer,
    AnswerStatus,
    Citation,
    Claim,
    EvidenceChunk,
    Question,
)


_DRAFTER_VERSION = "deterministic-local-v1"


def _normalize_whitespace(text: str) -> str:
    """Collapse whitespace without paraphrasing or changing punctuation."""

    return " ".join(text.split())


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{prefix}_{digest.hexdigest()[:24]}"


def _validated_evidence(
    question: Question,
    evidence: Sequence[EvidenceChunk],
) -> tuple[EvidenceChunk, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise TypeError("evidence must be a sequence of EvidenceChunk objects")

    chunks: list[EvidenceChunk] = []
    seen_chunk_ids: set[str] = set()
    for chunk in evidence:
        if not isinstance(chunk, EvidenceChunk):
            raise TypeError("evidence must contain only EvidenceChunk objects")
        if chunk.tenant_id != question.tenant_id:
            raise ValueError(
                f"evidence chunk {chunk.chunk_id!r} belongs to a different tenant"
            )
        if chunk.chunk_id in seen_chunk_ids:
            raise ValueError(
                f"duplicate evidence chunk_id {chunk.chunk_id!r} makes citations ambiguous"
            )
        if not _normalize_whitespace(chunk.text):
            raise ValueError(f"evidence chunk {chunk.chunk_id!r} has blank text")
        seen_chunk_ids.add(chunk.chunk_id)
        chunks.append(chunk)
    return tuple(chunks)


def draft(
    question: Question,
    evidence: Sequence[EvidenceChunk],
    max_claims: int = 3,
) -> Answer:
    """Build a conservative answer from only the supplied evidence.

    This checkpoint intentionally uses evidence text verbatim after whitespace
    normalization.  It is a transparent local baseline, not an LLM-backed
    answer writer.  Each selected evidence chunk becomes one claim with one
    exact citation.
    """

    if not isinstance(question, Question):
        raise TypeError("question must be a Question")
    if isinstance(max_claims, bool) or not isinstance(max_claims, int) or max_claims < 1:
        raise ValueError("max_claims must be a positive integer")

    chunks = _validated_evidence(question, evidence)
    if not chunks:
        answer_id = _stable_id("answer", question.tenant_id, question.question_id, "abstained")
        return Answer(
            tenant_id=question.tenant_id,
            answer_id=answer_id,
            question_id=question.question_id,
            status=AnswerStatus.DRAFTED,
            claims=[],
            abstained=True,
            abstain_reason="Insufficient evidence: no evidence chunks were supplied.",
            drafter_model_version=_DRAFTER_VERSION,
        )

    selected = chunks[:max_claims]
    selection_fingerprint = "".join(
        _stable_id(
            "evidence",
            chunk.chunk_id,
            chunk.doc_id,
            chunk.version_info.version,
            _normalize_whitespace(chunk.text),
        )
        for chunk in selected
    )
    answer_id = _stable_id(
        "answer",
        question.tenant_id,
        question.question_id,
        str(max_claims),
        selection_fingerprint,
    )

    claims: list[Claim] = []
    for position, chunk in enumerate(selected, start=1):
        claim_text = _normalize_whitespace(chunk.text)
        claim_id = _stable_id(
            "claim",
            answer_id,
            str(position),
            chunk.chunk_id,
            chunk.doc_id,
            chunk.version_info.version,
            claim_text,
        )
        citation = Citation(
            citation_id=_stable_id(
                "citation",
                claim_id,
                chunk.chunk_id,
                chunk.doc_id,
                chunk.version_info.version,
            ),
            claim_id=claim_id,
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            version=chunk.version_info.version,
        )
        claims.append(Claim(claim_id=claim_id, text=claim_text, citations=[citation]))

    return Answer(
        tenant_id=question.tenant_id,
        answer_id=answer_id,
        question_id=question.question_id,
        status=AnswerStatus.DRAFTED,
        claims=claims,
        abstained=False,
        drafter_model_version=_DRAFTER_VERSION,
    )
