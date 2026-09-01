"""Tests for independent, rule-based Phase 3 verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from trustilo.common.schemas import (
    Answer,
    AnswerStatus,
    Citation,
    Claim,
    EvidenceChunk,
    Question,
    SourceFormat,
    VersionInfo,
)
from trustilo.drafting import draft
from trustilo.verification import check


AS_OF = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


def _question(*, tenant_id: str = "tenant-a") -> Question:
    return Question(
        tenant_id=tenant_id,
        question_id="q-mfa",
        questionnaire_id="questionnaire-1",
        raw_text="Do you require MFA?",
        normalized_text="Do you require MFA?",
        source_format=SourceFormat.TEXT,
    )


def _chunk(
    chunk_id: str = "mfa",
    text: str = "MFA is required for privileged access.",
    *,
    tenant_id: str = "tenant-a",
    doc_id: str = "policy-1",
    version: str = "v2",
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> EvidenceChunk:
    return EvidenceChunk(
        tenant_id=tenant_id,
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=text,
        version_info=VersionInfo(
            version=version,
            source="synthetic_test",
            valid_from=valid_from,
            valid_until=valid_until,
        ),
    )


def _answer_with_claim(
    text: str,
    *,
    tenant_id: str = "tenant-a",
    claim_id: str = "claim-1",
    citation_claim_id: str = "claim-1",
    chunk_id: str = "mfa",
    doc_id: str = "policy-1",
    version: str = "v2",
) -> Answer:
    return Answer(
        tenant_id=tenant_id,
        answer_id="answer-1",
        question_id="q-mfa",
        status=AnswerStatus.DRAFTED,
        claims=[
            Claim(
                claim_id=claim_id,
                text=text,
                citations=[
                    Citation(
                        citation_id="citation-1",
                        claim_id=citation_claim_id,
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        version=version,
                    )
                ],
            )
        ],
    )


def _has_prefix(flags: list[str], prefix: str) -> bool:
    return any(flag.startswith(prefix) for flag in flags)


def test_fully_supported_generated_draft_verifies_at_one_with_stable_id() -> None:
    chunk = _chunk(text="  MFA is required\nfor privileged access. ")
    answer = draft(_question(), [chunk])

    first = check(answer, [chunk], as_of=AS_OF)
    second = check(answer, [chunk], as_of=AS_OF)

    assert first.support_score == 1.0
    assert first.contradiction_flags == []
    assert first.freshness_flags == []
    assert first.requested_requery is False
    assert first.requery_query is None
    assert first.verification_id == second.verification_id


def test_support_score_is_supported_claims_divided_by_total_claims() -> None:
    supported = _chunk("supported", "MFA is required.", doc_id="doc-supported")
    unsupported = _chunk("unsupported", "Backups are tested monthly.", doc_id="doc-unsupported")
    answer = Answer(
        tenant_id="tenant-a",
        answer_id="answer-two-claims",
        question_id="q-mfa",
        status=AnswerStatus.DRAFTED,
        claims=[
            Claim(
                claim_id="claim-supported",
                text="MFA is required.",
                citations=[
                    Citation(
                        citation_id="citation-supported",
                        claim_id="claim-supported",
                        chunk_id="supported",
                        doc_id="doc-supported",
                        version="v2",
                    )
                ],
            ),
            Claim(
                claim_id="claim-unsupported",
                text="Backups are tested weekly.",
                citations=[
                    Citation(
                        citation_id="citation-unsupported",
                        claim_id="claim-unsupported",
                        chunk_id="unsupported",
                        doc_id="doc-unsupported",
                        version="v2",
                    )
                ],
            ),
        ],
    )

    result = check(answer, [supported, unsupported], as_of=AS_OF)

    assert result.support_score == 0.5
    assert _has_prefix(result.contradiction_flags, "unsupported_claim:claim-unsupported")


def test_unsupported_and_mismatched_citation_fields_are_flagged() -> None:
    answer = _answer_with_claim(
        "MFA is optional for privileged access.",
        citation_claim_id="wrong-claim",
        doc_id="wrong-document",
        version="wrong-version",
    )

    result = check(answer, [_chunk()], as_of=AS_OF)

    assert result.support_score == 0.0
    assert _has_prefix(result.contradiction_flags, "citation_claim_mismatch:")
    assert _has_prefix(result.contradiction_flags, "citation_doc_mismatch:")
    assert _has_prefix(result.contradiction_flags, "citation_version_mismatch:")
    assert _has_prefix(result.contradiction_flags, "unsupported_claim:")
    assert any("required_vs_optional" in flag for flag in result.contradiction_flags)


def test_unresolved_citation_is_flagged() -> None:
    answer = _answer_with_claim("MFA is required.", chunk_id="missing")

    result = check(answer, [_chunk()], as_of=AS_OF)

    assert result.support_score == 0.0
    assert _has_prefix(result.contradiction_flags, "unresolved_citation:")


def test_text_support_does_not_match_inside_a_larger_word() -> None:
    answer = _answer_with_claim("FA is required for privileged access.")

    result = check(answer, [_chunk()], as_of=AS_OF)

    assert result.support_score == 0.0
    assert _has_prefix(result.contradiction_flags, "unsupported_claim:")


def test_expired_and_future_evidence_are_flagged_separately_from_support() -> None:
    expired = _chunk(
        "expired",
        "MFA is required.",
        doc_id="doc-expired",
        valid_until=AS_OF - timedelta(seconds=1),
    )
    future = _chunk(
        "future",
        "Access is reviewed quarterly.",
        doc_id="doc-future",
        valid_from=AS_OF + timedelta(seconds=1),
    )
    answer = draft(_question(), [expired, future])

    result = check(answer, [expired, future], as_of=AS_OF)

    assert result.support_score == 1.0
    assert _has_prefix(result.freshness_flags, "expired_evidence:")
    assert _has_prefix(result.freshness_flags, "future_evidence:")


def test_explicit_negation_contradiction_is_flagged() -> None:
    answer = _answer_with_claim("MFA is not required for privileged access.")

    result = check(answer, [_chunk()], as_of=AS_OF)

    assert result.support_score == 0.0
    assert any(flag.endswith(":negation") for flag in result.contradiction_flags)


def test_reordered_equivalent_clauses_do_not_create_a_polarity_conflict() -> None:
    answer = _answer_with_claim("MFA is required and guest access is optional.")
    evidence = _chunk(text="Guest access is optional; MFA is required.")

    result = check(answer, [evidence], as_of=AS_OF)

    assert result.support_score == 0.0
    assert _has_prefix(result.contradiction_flags, "unsupported_claim:")
    assert not _has_prefix(result.contradiction_flags, "contradiction:")


def test_direct_negation_is_detected_when_unrelated_evidence_also_says_not() -> None:
    answer = _answer_with_claim("MFA is not required. Accounts are monitored.")
    evidence = _chunk(text="MFA is required. Passwords are not shared.")

    result = check(answer, [evidence], as_of=AS_OF)

    assert result.support_score == 0.0
    assert any(flag.endswith(":negation") for flag in result.contradiction_flags)


def test_negated_opposite_polarity_is_not_a_false_contradiction() -> None:
    answer = _answer_with_claim("MFA is not optional.")
    evidence = _chunk(text="MFA is required.")

    result = check(answer, [evidence], as_of=AS_OF)

    assert result.support_score == 0.0
    assert _has_prefix(result.contradiction_flags, "unsupported_claim:")
    assert not _has_prefix(result.contradiction_flags, "contradiction:")


def test_abstention_is_safe_and_explicitly_marked() -> None:
    answer = draft(_question(), [])

    result = check(answer, [], as_of=AS_OF)

    assert result.support_score == 1.0
    assert result.contradiction_flags == ["abstention:no_claims_to_verify"]
    assert result.freshness_flags == []
    assert result.requested_requery is False


def test_abstention_with_uncited_partial_claim_is_not_treated_as_safe() -> None:
    answer = Answer(
        tenant_id="tenant-a",
        answer_id="answer-partial-uncited",
        question_id="q-mfa",
        status=AnswerStatus.DRAFTED,
        claims=[Claim(claim_id="claim-partial", text="MFA is optional.", citations=[])],
        abstained=True,
        abstain_reason="Only part of the question could be answered.",
    )

    result = check(answer, [], as_of=AS_OF)

    assert result.support_score == 0.0
    assert "abstention:partial_claims_present" in result.contradiction_flags
    assert "uncited_claim:claim-partial" in result.contradiction_flags
    assert "abstention:no_claims_to_verify" not in result.contradiction_flags


def test_abstention_with_cited_supported_partial_claim_is_still_verified() -> None:
    answer = _answer_with_claim("MFA is required for privileged access.").model_copy(
        update={
            "answer_id": "answer-partial-supported",
            "abstained": True,
            "abstain_reason": "The remaining question lacks evidence.",
        }
    )

    result = check(answer, [_chunk()], as_of=AS_OF)

    assert result.support_score == 1.0
    assert result.contradiction_flags == ["abstention:partial_claims_present"]


def test_cross_tenant_evidence_is_rejected_before_verification() -> None:
    answer = _answer_with_claim("MFA is required for privileged access.")

    with pytest.raises(ValueError, match="different tenant"):
        check(answer, [_chunk(tenant_id="tenant-b")], as_of=AS_OF)


def test_duplicate_chunk_identifiers_are_rejected_as_ambiguous() -> None:
    answer = _answer_with_claim("MFA is required for privileged access.")

    with pytest.raises(ValueError, match="duplicate evidence chunk_id"):
        check(answer, [_chunk(), _chunk(text="MFA is optional.")], as_of=AS_OF)


def test_as_of_and_evidence_validity_bounds_must_be_timezone_aware() -> None:
    answer = _answer_with_claim("MFA is required for privileged access.")

    with pytest.raises(ValueError, match="as_of must be timezone-aware"):
        check(answer, [_chunk()], as_of=datetime(2026, 8, 1))

    naive_chunk = _chunk(valid_until=datetime(2026, 8, 2))
    with pytest.raises(ValueError, match="valid_until.*timezone-aware"):
        check(answer, [naive_chunk], as_of=AS_OF)


def test_verification_does_not_mutate_answer_or_evidence() -> None:
    chunk = _chunk()
    answer = draft(_question(), [chunk])
    answer_before = answer.model_dump()
    chunk_before = chunk.model_dump()

    check(answer, [chunk], as_of=AS_OF)

    assert answer.model_dump() == answer_before
    assert chunk.model_dump() == chunk_before
