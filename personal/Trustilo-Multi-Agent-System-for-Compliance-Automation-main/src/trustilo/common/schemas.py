"""Canonical Trustilo data model.

This module and `specs/02-data-model.md` must stay in sync — if you
change one, change the other in the same commit (see
`.cursor/rules/data-model-and-versioning.mdc`).

Every stage in `src/trustilo/` passes these objects between each
other. Do not invent parallel ad hoc dict/tuple representations for
the same concepts elsewhere in the codebase.

Validators here encode requirements that are load-bearing, not
stylistic:
  - FR3: every EvidenceChunk carries doc_id, version, source, tenant_id.
  - NFR1/FR6: a Claim without citations is only valid on an abstained Answer.
  - NFR9: an "escalate" EscalationDecision must carry reason_codes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Shared building blocks
# --------------------------------------------------------------------------


class ConfidentialityLabel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class TenantScoped(BaseModel):
    """Mixin: every entity that can be evidence-derived or customer-specific
    carries a tenant namespace (NFR2). Never give this a default —
    forcing every construction site to state the tenant explicitly is
    what makes a missing-filter bug loud instead of silent.
    """

    tenant_id: str = Field(..., min_length=1)


class VersionInfo(BaseModel):
    """Version/provenance metadata required on every evidence-derived
    object (FR3's literal success criterion)."""

    version: str = Field(..., min_length=1, description="Sortable/comparable version tag, e.g. an ISO date or monotonic tag")
    source: str = Field(..., min_length=1, description="Where this came from, e.g. 'customer_upload', 'pentest_report_2026Q2'")
    owner: str | None = Field(default=None, description="Who owns/approved this evidence within the customer org")
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidentiality_label: ConfidentialityLabel = ConfidentialityLabel.CONFIDENTIAL


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------


class EvidenceDocType(str, Enum):
    POLICY = "policy"
    ARCHITECTURE = "architecture"
    AUDIT_EXTRACT = "audit_extract"
    PENTEST_SUMMARY = "pentest_summary"
    PRIOR_APPROVED_ANSWER = "prior_approved_answer"
    OTHER = "other"


class EvidenceDocument(TenantScoped):
    doc_id: str
    doc_type: EvidenceDocType
    title: str
    version_info: VersionInfo
    storage_uri: str = Field(..., description="Where the source file lives in object storage")
    superseded_by: str | None = Field(default=None, description="doc_id of the newer version, if any — old docs are never deleted, only superseded")
    created_at: datetime = Field(default_factory=_utcnow)


class EvidenceChunk(TenantScoped):
    """A retrievable, citable slice of an EvidenceDocument.

    FR3 hard rule: doc_id, version_info.version, version_info.source,
    and tenant_id must all be present — enforced by field requiredness
    plus the validator below, not left to convention.
    """

    chunk_id: str
    doc_id: str
    text: str = Field(..., min_length=1)
    embedding_ref: str | None = Field(default=None, description="Pointer to the stored embedding, e.g. a vector-store row id")
    version_info: VersionInfo
    framework_refs: list[str] = Field(default_factory=list, description="Post-MVP: optional framework control identifiers, e.g. NIST CSF subcategories")

    @model_validator(mode="after")
    def _fr3_required_provenance(self) -> "EvidenceChunk":
        if not self.doc_id or not self.version_info.version or not self.version_info.source or not self.tenant_id:
            raise ValueError(
                "EvidenceChunk requires doc_id, version_info.version, version_info.source, "
                "and tenant_id (FR3) — evidence without provenance cannot be cited"
            )
        return self


# --------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------


class SourceFormat(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"
    TEXT = "text"


class Question(TenantScoped):
    question_id: str
    questionnaire_id: str
    raw_text: str
    normalized_text: str | None = None
    section: str | None = None
    domain_label: str | None = Field(default=None, description="e.g. a CCM domain — see specs/glossary.md")
    answer_type: str | None = None
    duplicate_of: str | None = Field(default=None, description="question_id of a prior near-duplicate, if classified as one (FR2)")
    source_format: SourceFormat
    source_row_index: int | None = Field(default=None, description="Original row/cell index for XLSX/CSV round-trip export (FR10)")


# --------------------------------------------------------------------------
# Answers, Claims, Citations
# --------------------------------------------------------------------------


class Citation(BaseModel):
    citation_id: str
    claim_id: str
    chunk_id: str
    doc_id: str
    version: str


class Claim(BaseModel):
    claim_id: str
    text: str = Field(..., min_length=1)
    citations: list[Citation] = Field(default_factory=list)


class AnswerStatus(str, Enum):
    INTAKE_PENDING = "intake_pending"
    CLASSIFIED = "classified"
    RETRIEVED = "retrieved"
    DRAFTED = "drafted"
    VERIFYING = "verifying"
    RETRIEVAL_RETRY = "retrieval_retry"
    VERIFIED = "verified"
    AUTO_FINALIZED = "auto_finalized"
    ESCALATED = "escalated"
    REVIEWER_APPROVED = "reviewer_approved"
    REVIEWER_EDITED = "reviewer_edited"
    REVIEWER_REJECTED = "reviewer_rejected"
    FINALIZED = "finalized"


class Answer(TenantScoped):
    answer_id: str
    question_id: str
    status: AnswerStatus = AnswerStatus.INTAKE_PENDING
    claims: list[Claim] = Field(default_factory=list)
    abstained: bool = False
    abstain_reason: str | None = None
    drafter_model_version: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _uncited_claim_requires_abstention(self) -> "Answer":
        # FR5/FR6/NFR1: a claim with zero citations is only valid when
        # the whole answer is an abstention. This is the single most
        # important invariant in the codebase — see
        # .cursor/agents/groundedness-reviewer.md.
        if not self.abstained:
            for claim in self.claims:
                if not claim.citations:
                    raise ValueError(
                        f"Claim {claim.claim_id!r} has no citations but Answer.abstained is False — "
                        "every claim in a non-abstained answer must cite evidence (FR5, FR6, NFR1)"
                    )
        if self.abstained and not self.abstain_reason:
            raise ValueError("An abstained Answer must include abstain_reason")
        return self


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


class VerificationResult(BaseModel):
    verification_id: str
    answer_id: str
    support_score: float = Field(..., ge=0.0, le=1.0)
    contradiction_flags: list[str] = Field(default_factory=list)
    freshness_flags: list[str] = Field(default_factory=list)
    consistent_with_prior: bool | None = Field(default=None, description="None if there was no comparable prior approved answer to check against")
    requested_requery: bool = False
    requery_query: str | None = None
    verifier_model_version: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _requery_needs_a_query(self) -> "VerificationResult":
        if self.requested_requery and not self.requery_query:
            raise ValueError("requested_requery=True requires a non-empty requery_query")
        return self


# --------------------------------------------------------------------------
# Escalation & human review
# --------------------------------------------------------------------------


class EscalationOutcome(str, Enum):
    AUTO_FINALIZE = "auto_finalize"
    ESCALATE = "escalate"


class EscalationDecision(BaseModel):
    decision_id: str
    answer_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    decision: EscalationOutcome
    reason_codes: list[str] = Field(default_factory=list)
    human_readable_reason: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _escalation_needs_reason_codes(self) -> "EscalationDecision":
        # NFR9: every escalated task has a machine-readable reason code.
        if self.decision == EscalationOutcome.ESCALATE and not self.reason_codes:
            raise ValueError("decision='escalate' requires at least one reason code (NFR9)")
        return self


class ReviewOutcome(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    REQUEST_EVIDENCE = "request_evidence"


class ReviewTask(TenantScoped):
    task_id: str
    answer_id: str
    reason_codes: list[str]
    assigned_reviewer: str | None = None
    status: ReviewOutcome = ReviewOutcome.PENDING
    reviewer_decision: str | None = None
    corrected_answer_id: str | None = Field(default=None, description="answer_id of the reviewer-edited replacement, if status == 'edited'")
    resolved_at: datetime | None = None


# --------------------------------------------------------------------------
# Audit trail
# --------------------------------------------------------------------------


class PipelineStage(str, Enum):
    INTAKE = "intake"
    CLASSIFICATION = "classification"
    RETRIEVAL = "retrieval"
    DRAFTING = "drafting"
    VERIFICATION = "verification"
    ESCALATION = "escalation"
    HUMAN_REVIEW = "human_review"
    EXPORT = "export"
    FRAMEWORK_MAPPING = "framework_mapping"  # post-MVP


class AuditEvent(TenantScoped):
    """One immutable record of a state transition (NFR3).

    A finalized Answer must be reconstructable purely from its
    AuditEvent chain — see specs/03-orchestrator.md.
    """

    event_id: str
    question_id: str
    stage: PipelineStage
    payload_ref: str = Field(..., description="Pointer to the full payload (e.g. a blob/row id) — keep the event itself small")
    actor: str = Field(..., description="Agent/model version or human reviewer id that produced this event")
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------
# Experiment configuration (evaluation)
# --------------------------------------------------------------------------


class BaselineName(str, Enum):
    B0_DIRECT_LLM = "B0"
    B1_SINGLE_AGENT_RAG = "B1"
    B2_RAG_PLUS_VERIFIER = "B2"
    P_TRUSTILO = "P"


class ExperimentConfig(BaseModel):
    """Frozen configuration for one benchmark/ablation run.

    Every Answer/VerificationResult/EscalationDecision produced during
    a run should record this config_id, so a metric change can be
    attributed to a specific component swap (NFR7).
    """

    config_id: str
    baseline_name: BaselineName
    model_ids: dict[str, str] = Field(default_factory=dict, description="e.g. {'drafting': 'claude-...', 'verification': 'claude-...'}")
    retriever_config: dict[str, str | int | bool] = Field(default_factory=dict, description="e.g. {'mode': 'hybrid', 'rerank': True, 'top_k': 10}")
    verifier_config: dict[str, str | int | bool] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict, description="Escalation thresholds — must be frozen before a held-out test run")
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------
# Orchestrator state bundle
# --------------------------------------------------------------------------


class PipelineState(BaseModel):
    """What the Orchestrator threads through each stage function.

    Stages are pure functions of this object plus an ExperimentConfig
    (see specs/03-orchestrator.md) — nothing else should be implicit
    global state.
    """

    question: Question
    evidence: list[EvidenceChunk] = Field(default_factory=list)
    answer: Answer | None = None
    verification: VerificationResult | None = None
    escalation: EscalationDecision | None = None
    retry_used: bool = False
