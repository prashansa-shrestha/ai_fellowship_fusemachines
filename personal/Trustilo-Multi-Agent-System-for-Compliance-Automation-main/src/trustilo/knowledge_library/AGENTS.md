# AGENTS.md — knowledge_library

Owns: **FR3** (knowledge ingestion) and the versioning half of
**NFR2**/**NFR3**. Full spec: `../../../specs/02-data-model.md`
(entities), `../../../specs/12-security-and-governance.md` (handling
rules).

- Chunking + indexing must stamp every `EvidenceChunk` with `doc_id`,
  `version_info.version`, `version_info.source`, and `tenant_id` — the
  schema validator in `common/schemas.py` will reject anything
  missing these, so a bug here fails loudly, not silently.
- Re-uploading a document creates a new `EvidenceDocument` version;
  the old one's chunks are marked superseded, never deleted — existing
  citations in already-finalized answers must keep resolving.
- This package also backs the Approved-Edit Reuse Store
  (`specs/10-export-audit-feedback.md`, FR11): an approved reviewer
  edit becomes a new `EvidenceChunk` of type
  `prior_approved_answer`, subject to the same tenant/version rules as
  any other evidence — don't build a separate storage path for it.
