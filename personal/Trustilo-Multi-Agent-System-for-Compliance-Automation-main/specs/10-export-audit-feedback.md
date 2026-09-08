# 10 — Export, Audit Trail & Feedback Capture

Status: living document. Owns: **FR10** (export/report), **FR11**
(feedback capture), **NFR3** (auditability, cross-referenced from
`specs/03-orchestrator.md`).

## FR10 — Export and report

Export answers plus a coverage/confidence report; write back to XLSX
where the original format is programmatically writable.

- **Success criterion:** no answer/question misalignment in
  round-trip XLSX tests. Concretely: ingest an XLSX questionnaire,
  run it through the pipeline, export back to XLSX, and assert every
  answer lands in the same row/column as its source question came
  from. This is why `specs/04-intake-classification.md` requires
  preserving the source row index at ingestion time.
- The coverage/confidence report is a separate artifact from the
  filled questionnaire — it summarizes auto-finalized vs. escalated
  counts, confidence distribution, and per-domain coverage, so a
  customer-facing stakeholder can see pipeline health without reading
  every answer.

## NFR3 — Auditability (the export/reporting side of it)

Every finalized answer must expose its full lineage on request:
question → retrieved evidence → draft → verification → (escalation +
reviewer decision, if any) → final answer, with version IDs at each
step. Build an `audit.reconstruct(answer_id) -> AuditTrail` function
early and write a test that runs it over every finalized answer in the
benchmark — 100% must resolve cleanly (NFR3's literal target).

## FR11 — Feedback capture

Save approved edits as curated examples for later retrieval/reuse.

- **Success criterion:** an approved edit is retrievable by a
  semantically similar later question.
- This is **not** a fine-tuning loop (explicitly out of MVP scope —
  see `specs/00-overview-and-mvp-scope.md`). It's a versioned addition
  to the retrievable evidence pool: an approved, edited `Answer`
  becomes (or generates) an `EvidenceChunk` tagged as a prior-approved-
  answer type, subject to the same tenant/version rules as any other
  evidence.
- The Approved-Edit Reuse Store therefore reuses `EvidenceChunk`
  machinery rather than inventing a parallel storage system — see
  `specs/02-data-model.md`.

## Interfaces

```
export.to_original_format(questionnaire_id: str, answers: list[Answer]) -> bytes
export.coverage_report(questionnaire_id: str) -> CoverageReport
audit.reconstruct(answer_id: str) -> AuditTrail
feedback.capture_approved_edit(review_task: ReviewTask) -> EvidenceChunk
```
