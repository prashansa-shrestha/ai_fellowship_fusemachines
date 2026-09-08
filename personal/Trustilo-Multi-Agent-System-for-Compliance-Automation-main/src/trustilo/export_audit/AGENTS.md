# AGENTS.md — export_audit

Owns: **FR10** (export/report), **FR11** (feedback capture), and the
reconstruction side of **NFR3** (auditability). Full spec:
`../../../specs/10-export-audit-feedback.md`.

- XLSX round-trip export must place each answer in the same
  row/column its source question came from — this depends on
  `Question.source_row_index` being preserved by `intake/` at
  ingestion time; don't try to re-derive alignment here.
- `audit.reconstruct(answer_id)` must resolve 100% of finalized
  answers purely from the `AuditEvent` chain — write this function
  early and test it against every finalized answer in the benchmark,
  not just a hand-picked example.
- `feedback.capture_approved_edit()` produces an `EvidenceChunk`
  (via `knowledge_library/`), not a training example — this is
  explicitly not a fine-tuning loop (see
  `../../../specs/00-overview-and-mvp-scope.md`).
