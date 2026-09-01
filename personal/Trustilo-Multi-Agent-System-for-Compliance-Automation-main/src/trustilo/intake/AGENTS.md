# AGENTS.md — intake

Owns: **FR1** (ingestion), **FR2** (classification). Full spec:
`../../../specs/04-intake-classification.md`.

- Deterministic normalization happens before any LLM call touches the
  text — don't let a model "clean up" formatting as part of parsing.
- Preserve `source_row_index` on every `Question` parsed from XLSX/CSV
  — the FR10 export round-trip depends on it.
- `parse()` and `classify()` are separate, pure functions — don't
  merge them into one call, since the Orchestrator needs to persist
  state between them (see `specs/01-architecture.md`'s state machine:
  `INTAKE_PENDING → CLASSIFIED`).
- A parsing failure should produce a flagged/low-confidence `Question`
  record, not a silently mangled one or a crash that takes down the
  whole questionnaire's processing.
