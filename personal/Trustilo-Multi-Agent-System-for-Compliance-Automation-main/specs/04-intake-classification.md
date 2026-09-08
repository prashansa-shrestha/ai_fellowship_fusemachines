# 04 — Intake & Classification

Status: living document. Owns: **FR1** (ingestion), **FR2**
(classification).

## FR1 — Questionnaire ingestion

Parse PDF, XLSX/CSV, and plain text into ordered `Question` records,
preserving IDs/sections where the source format provides them.

- **Success criterion:** ≥95% extraction correctness on the curated
  format test set (a fixed set of representative real-shaped
  questionnaires you build early and never silently modify).
- Deterministic normalization happens **before** any LLM call touches
  the text — don't let an LLM "clean up" formatting as part of
  extraction; that makes extraction errors non-reproducible.
- PDF tables and scans are the expected hard case — OCR only where
  necessary (most CAIQ-style PDFs are text-native), and log a
  low-confidence-extraction flag per question rather than silently
  guessing at row alignment.
- XLSX/CSV: preserve the source row index in `Question.raw_text`
  metadata so `specs/10-export-audit-feedback.md`'s round-trip export
  can realign answers to the original spreadsheet.

## FR2 — Question classification

Tag each `Question` with: domain, question type, answer type, and a
novelty/duplicate similarity score against previously-seen questions
(within the same tenant).

- **Success criterion:** ≥85% macro-F1 for domain labels on an
  SME-labelled subset, or an explicitly agreed simpler accuracy metric
  if the class set turns out very small (record which metric you used
  and why in `specs/14-requirements-traceability.md`).
- Duplicate/novelty detection is what lets Retrieval and the Approved-
  Edit Reuse Store (`specs/10-export-audit-feedback.md`) short-circuit
  to a previously-approved answer instead of redrafting from scratch —
  treat it as a first-class output, not a side effect.
- Domain taxonomy should track CAIQ's 17 CCM domains where applicable
  (see `specs/glossary.md`) so classification results are directly
  usable for stratifying the benchmark in
  `specs/11-evaluation-and-baselines.md`.

## Interface

```
intake.parse(raw_file: bytes, source_format: Literal["pdf","xlsx","csv","text"], tenant_id: str) -> list[Question]
intake.classify(question: Question) -> Question  # fills domain_label, answer_type, duplicate_of
```

Both functions are synchronous/pure given their inputs — no shared
mutable state, so they're trivially testable and safe to retry
(consistent with the Orchestrator's idempotency contract).

## Common failure modes to design tests for

From the paper's error taxonomy (`specs/11-evaluation-and-baselines.md`):
**ingestion/parsing error** should be a distinct, loggable category —
don't let a parsing failure surface downstream as a retrieval miss or
an unsupported-claim finding. If Intake can't confidently extract a
question, it should flag it rather than pass a mangled question
further down the pipeline.
