"""Tests for deterministic, citation-safe Phase 3 drafting."""

from __future__ import annotations

import pytest

from trustilo.common.schemas import AnswerStatus, EvidenceChunk, Question, SourceFormat, VersionInfo
from trustilo.drafting import draft


def _question(*, tenant_id: str = "tenant-a") -> Question:
    return Question(
        tenant_id=tenant_id,
        question_id="q-mfa",
        questionnaire_id="questionnaire-1",
        raw_text="Do you require MFA for privileged access?",
        normalized_text="Do you require MFA for privileged access?",
        source_format=SourceFormat.TEXT,
    )


def _chunk(
    chunk_id: str,
    text: str,
    *,
    tenant_id: str = "tenant-a",
    doc_id: str | None = None,
    version: str = "2026-01-01",
) -> EvidenceChunk:
    return EvidenceChunk(
        tenant_id=tenant_id,
        chunk_id=chunk_id,
        doc_id=doc_id or f"doc-{chunk_id}",
        text=text,
        version_info=VersionInfo(version=version, source="synthetic_test"),
    )


def test_draft_uses_normalized_evidence_verbatim_with_exact_citations() -> None:
    chunks = [
        _chunk("mfa", " Privileged  access\nrequires MFA. ", doc_id="policy-7", version="v3"),
        _chunk("review", "Privileged access is reviewed quarterly."),
    ]

    answer = draft(_question(), chunks)

    assert answer.status is AnswerStatus.DRAFTED
    assert answer.abstained is False
    assert [claim.text for claim in answer.claims] == [
        "Privileged access requires MFA.",
        "Privileged access is reviewed quarterly.",
    ]
    first_citation = answer.claims[0].citations[0]
    assert first_citation.claim_id == answer.claims[0].claim_id
    assert (first_citation.chunk_id, first_citation.doc_id, first_citation.version) == (
        "mfa",
        "policy-7",
        "v3",
    )


def test_draft_limits_claims_and_produces_stable_ids() -> None:
    chunks = [
        _chunk("one", "MFA is required."),
        _chunk("two", "Access is reviewed quarterly."),
    ]

    first = draft(_question(), chunks, max_claims=1)
    second = draft(_question(), chunks, max_claims=1)

    assert len(first.claims) == 1
    assert first.answer_id == second.answer_id
    assert first.claims[0].claim_id == second.claims[0].claim_id
    assert first.claims[0].citations[0].citation_id == second.claims[0].citations[0].citation_id


def test_no_evidence_returns_an_explicit_abstention() -> None:
    answer = draft(_question(), [])

    assert answer.status is AnswerStatus.DRAFTED
    assert answer.abstained is True
    assert answer.claims == []
    assert answer.abstain_reason is not None
    assert "Insufficient evidence" in answer.abstain_reason


def test_cross_tenant_evidence_is_rejected_before_drafting() -> None:
    with pytest.raises(ValueError, match="different tenant"):
        draft(_question(tenant_id="tenant-a"), [_chunk("foreign", "MFA.", tenant_id="tenant-b")])


def test_duplicate_chunk_identifiers_are_rejected_as_ambiguous() -> None:
    with pytest.raises(ValueError, match="duplicate evidence chunk_id"):
        draft(
            _question(),
            [
                _chunk("duplicate", "MFA is required.", doc_id="policy-a"),
                _chunk("duplicate", "MFA is optional.", doc_id="policy-b"),
            ],
        )


def test_whitespace_only_evidence_is_rejected_before_claim_construction() -> None:
    with pytest.raises(ValueError, match="blank text"):
        draft(_question(), [_chunk("blank", "   \n  ")])


@pytest.mark.parametrize("max_claims", [0, -1, 1.5, True])
def test_max_claims_must_be_a_positive_integer(max_claims: object) -> None:
    with pytest.raises(ValueError, match="max_claims"):
        draft(_question(), [], max_claims=max_claims)  # type: ignore[arg-type]


def test_draft_does_not_mutate_question_or_evidence() -> None:
    question = _question()
    chunks = [_chunk("mfa", "MFA is required.")]
    question_before = question.model_dump()
    chunks_before = [chunk.model_dump() for chunk in chunks]

    draft(question, chunks)

    assert question.model_dump() == question_before
    assert [chunk.model_dump() for chunk in chunks] == chunks_before
