# 02 — Data Model

Status: living document. Source: `report/main.tex` §III.A, §V.B item 1.
Canonical implementation: `src/trustilo/common/schemas.py` — this spec
and that file must stay in sync; if you change one, change the other
in the same commit.

## The four kinds of data (per the paper's Data Identification)

1. **Question data** — questions, sections, expected answer formats,
   domain labels.
2. **Evidence data** — policy passages, control descriptions,
   architecture/security statements, audit evidence summaries,
   approved historical answers.
3. **Evaluation labels** — evidence-relevance labels, gold answers,
   claim-support labels, contradiction/staleness flags, "needs human
   review" labels.
4. **Framework metadata** — public/licensed control identifiers and
   mappings, used only by the post-MVP mapping experiment.

## Core entities

Every entity below carries `tenant_id` (customer namespace, NFR2) and,
where it represents evidence-derived content, `version` metadata
(source, owner, effective/valid dates, confidentiality label — FR3).

| Entity | Purpose | Key fields |
|---|---|---|
| `EvidenceDocument` | An uploaded source document | `doc_id`, `tenant_id`, `doc_type`, `source`, `owner`, `version`, `valid_from`, `valid_until`, `confidentiality_label`, `storage_uri` |
| `EvidenceChunk` | A retrievable, citable slice of a document | `chunk_id`, `doc_id`, `tenant_id`, `text`, `embedding_ref`, denormalized version fields |
| `Question` | A normalized questionnaire item | `question_id`, `questionnaire_id`, `tenant_id`, `raw_text`, `normalized_text`, `section`, `domain_label`, `answer_type`, `duplicate_of`, `source_format` |
| `Claim` | One atomic assertion inside an answer | `claim_id`, `text`, `citations: list[Citation]` |
| `Citation` | A pointer from a claim to specific evidence | `citation_id`, `chunk_id`, `doc_id`, `version`, `claim_id` |
| `Answer` | A drafted/finalized response to a question | `answer_id`, `question_id`, `tenant_id`, `status`, `claims`, `abstained`, `abstain_reason`, `drafter_model_version` |
| `VerificationResult` | Independent check of an `Answer` | `verification_id`, `answer_id`, `support_score`, `contradiction_flags`, `freshness_flags`, `consistent_with_prior`, `requested_requery`, `requery_query`, `verifier_model_version` |
| `EscalationDecision` | The confidence/risk call on a verified answer | `decision_id`, `answer_id`, `confidence_score`, `decision` (`auto_finalize`\|`escalate`), `reason_codes: list[str]`, `human_readable_reason` |
| `ReviewTask` | Work item for a human reviewer | `task_id`, `answer_id`, `tenant_id`, `reason_codes`, `assigned_reviewer`, `status`, `reviewer_decision`, `corrected_answer_id`, `resolved_at` |
| `AuditEvent` | One immutable record of a state transition | `event_id`, `tenant_id`, `question_id`, `stage`, `payload_ref`, `actor`, `created_at` |
| `ExperimentConfig` | Frozen config for one benchmark/ablation run | `config_id`, `baseline_name` (B0\|B1\|B2\|P), `model_ids`, `retriever_config`, `verifier_config`, `thresholds`, `created_at` |

## Non-negotiable field rules

- **`EvidenceChunk` without `doc_id`, `version`, `source`, or
  `tenant_id` must fail validation.** This is FR3's explicit success
  criterion ("every indexed chunk has document ID, version, source,
  and customer namespace") — it's not a nice-to-have, it's a hard
  constraint enforced in the schema, not just in a code review.
- **A `Claim` with zero `citations` is only valid when the parent
  `Answer.abstained is True`.** Otherwise it's an unsupported claim by
  definition — enforce this as a validator, not a convention teams are
  expected to remember.
- **`EscalationDecision.reason_codes` must be non-empty when
  `decision == "escalate"`.** NFR9 requires a machine-readable reason
  for every escalation, not just a human-readable sentence.
- **IDs are opaque strings you control (e.g. ULIDs), not
  auto-increment integers**, so ID generation can happen client-side
  before a row is persisted (useful for idempotent retries — see
  `specs/03-orchestrator.md`).

## Status enum for `Answer`

```
INTAKE_PENDING, CLASSIFIED, RETRIEVED, DRAFTED, VERIFYING,
RETRIEVAL_RETRY, VERIFIED, AUTO_FINALIZED, ESCALATED,
REVIEWER_APPROVED, REVIEWER_EDITED, REVIEWER_REJECTED, FINALIZED
```

See `specs/01-architecture.md` for the allowed transitions between
these.

## Versioning conventions

- `version` is a string you can sort/compare (e.g. an ISO date or a
  monotonically increasing tag), not a free-text field.
- When a document is re-uploaded with a new version, previous
  `EvidenceChunk` rows are **not** deleted — they're marked
  superseded, so existing citations in already-finalized `Answer`
  rows still resolve (auditability survives evidence updates).
- Freshness checks in Verification compare `EvidenceChunk.version` /
  `valid_until` against "now," not against the `Question`'s ingestion
  date.

## Extending this model

Adding a field: extend the Pydantic model in `schemas.py`, update the
table above in the same change, and note in the commit message which
FR/NFR (if any) motivated it. Don't add fields "just in case" —
everything here traces back to a requirement in
`specs/14-requirements-traceability.md`.
