"""Tests for src/trustilo/common/schemas.py.

These are deliberately validator-focused: the whole point of putting
invariants like "no uncited claim" and "escalations need reason codes"
into Pydantic validators (rather than code-review conventions) is that
they're impossible to construct incorrectly. These tests prove that.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from trustilo.common.schemas import (
    Answer,
    Citation,
    Claim,
    ConfidentialityLabel,
    EscalationDecision,
    EscalationOutcome,
    EvidenceChunk,
    EvidenceDocType,
    Question,
    SourceFormat,
    VerificationResult,
    VersionInfo,
)


def make_version_info(**overrides) -> VersionInfo:
    defaults = dict(version="2026-01-01", source="customer_upload")
    defaults.update(overrides)
    return VersionInfo(**defaults)


def make_chunk(**overrides) -> EvidenceChunk:
    defaults = dict(
        tenant_id="tenant-a",
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="Access to production systems requires MFA.",
        version_info=make_version_info(),
    )
    defaults.update(overrides)
    return EvidenceChunk(**defaults)


class TestEvidenceChunkProvenance:
    """FR3: every indexed chunk has document ID, version, source, and tenant."""

    def test_valid_chunk_constructs(self):
        chunk = make_chunk()
        assert chunk.doc_id == "doc-1"
        assert chunk.tenant_id == "tenant-a"

    def test_missing_tenant_id_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceChunk(
                tenant_id="",
                chunk_id="chunk-1",
                doc_id="doc-1",
                text="some evidence",
                version_info=make_version_info(),
            )

    def test_missing_version_rejected(self):
        with pytest.raises(ValidationError):
            make_version_info(version="")

    def test_missing_source_rejected(self):
        with pytest.raises(ValidationError):
            make_version_info(source="")

    def test_confidentiality_defaults_to_confidential(self):
        # secure-by-default: evidence should never silently default to public
        info = make_version_info()
        assert info.confidentiality_label == ConfidentialityLabel.CONFIDENTIAL


class TestAnswerGroundingInvariant:
    """FR5/FR6/NFR1: no claim without a citation, unless the answer abstains."""

    def test_cited_claim_is_valid(self):
        answer = Answer(
            tenant_id="tenant-a",
            answer_id="ans-1",
            question_id="q-1",
            claims=[
                Claim(
                    claim_id="c1",
                    text="MFA is required for production access.",
                    citations=[
                        Citation(citation_id="cit-1", claim_id="c1", chunk_id="chunk-1", doc_id="doc-1", version="2026-01-01")
                    ],
                )
            ],
        )
        assert len(answer.claims[0].citations) == 1

    def test_uncited_claim_on_non_abstained_answer_is_rejected(self):
        with pytest.raises(ValidationError, match="no citations"):
            Answer(
                tenant_id="tenant-a",
                answer_id="ans-1",
                question_id="q-1",
                abstained=False,
                claims=[Claim(claim_id="c1", text="MFA is required.", citations=[])],
            )

    def test_abstained_answer_with_no_claims_is_valid(self):
        answer = Answer(
            tenant_id="tenant-a",
            answer_id="ans-1",
            question_id="q-1",
            abstained=True,
            abstain_reason="No matching evidence retrieved for this control.",
            claims=[],
        )
        assert answer.abstained is True

    def test_abstained_answer_without_reason_is_rejected(self):
        with pytest.raises(ValidationError, match="abstain_reason"):
            Answer(
                tenant_id="tenant-a",
                answer_id="ans-1",
                question_id="q-1",
                abstained=True,
                abstain_reason=None,
                claims=[],
            )

    def test_abstained_answer_can_still_have_uncited_claims(self):
        # abstained is the escape hatch — but this is an edge case teams
        # should generally avoid (an abstention should usually have zero
        # claims); the schema permits it because "abstained but partial
        # claims" is a legitimate reviewer-facing state in some designs.
        answer = Answer(
            tenant_id="tenant-a",
            answer_id="ans-1",
            question_id="q-1",
            abstained=True,
            abstain_reason="Partial evidence only.",
            claims=[Claim(claim_id="c1", text="Some uncited partial claim.", citations=[])],
        )
        assert answer.abstained is True


class TestEscalationExplainability:
    """NFR9: every escalated task needs a machine-readable reason code."""

    def test_escalate_without_reason_codes_is_rejected(self):
        with pytest.raises(ValidationError, match="reason code"):
            EscalationDecision(
                decision_id="dec-1",
                answer_id="ans-1",
                confidence_score=0.4,
                decision=EscalationOutcome.ESCALATE,
                reason_codes=[],
            )

    def test_escalate_with_reason_codes_is_valid(self):
        decision = EscalationDecision(
            decision_id="dec-1",
            answer_id="ans-1",
            confidence_score=0.4,
            decision=EscalationOutcome.ESCALATE,
            reason_codes=["MISSING_EVIDENCE"],
        )
        assert decision.reason_codes == ["MISSING_EVIDENCE"]

    def test_auto_finalize_does_not_require_reason_codes(self):
        decision = EscalationDecision(
            decision_id="dec-1",
            answer_id="ans-1",
            confidence_score=0.95,
            decision=EscalationOutcome.AUTO_FINALIZE,
            reason_codes=[],
        )
        assert decision.decision == EscalationOutcome.AUTO_FINALIZE


class TestVerificationRequery:
    def test_requery_without_query_text_is_rejected(self):
        with pytest.raises(ValidationError, match="requery_query"):
            VerificationResult(
                verification_id="v-1",
                answer_id="ans-1",
                support_score=0.3,
                requested_requery=True,
                requery_query=None,
            )

    def test_requery_with_query_text_is_valid(self):
        result = VerificationResult(
            verification_id="v-1",
            answer_id="ans-1",
            support_score=0.3,
            requested_requery=True,
            requery_query="MFA requirement for production database access",
        )
        assert result.requery_query is not None

    def test_support_score_out_of_range_is_rejected(self):
        with pytest.raises(ValidationError):
            VerificationResult(verification_id="v-1", answer_id="ans-1", support_score=1.5)


class TestQuestion:
    def test_minimal_question_constructs(self):
        q = Question(
            tenant_id="tenant-a",
            question_id="q-1",
            questionnaire_id="caiq-lite-run-1",
            raw_text="Does the organization enforce MFA for privileged access?",
            source_format=SourceFormat.XLSX,
            source_row_index=12,
        )
        assert q.source_row_index == 12
        assert q.duplicate_of is None
