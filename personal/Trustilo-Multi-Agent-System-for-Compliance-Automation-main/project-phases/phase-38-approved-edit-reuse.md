# Phase 38 — Approved-edit reuse

**Feature branch:** `codex/feature-38-approved-edit-reuse`  
**Depends on:** Phases 07, 13, and 35  
**Traceability:** `specs/10-export-audit-feedback.md`; FR11, NFR2

## Goal

Capture reviewer-approved edits as versioned evidence exemplars that similar later questions can retrieve.

## Implementation

- Convert an approved edited answer into an `EvidenceChunk` tagged as prior-approved Q/A.
- Preserve tenant, reviewer decision, source answer/task, version, and approval timestamps.
- Index through the existing knowledge-library path rather than a parallel store.
- Make inclusion configurable for the required with/without reuse ablation; never trigger autonomous fine-tuning.

## Unit and integration tests

- Only approved edits are captured; reject/request-evidence outcomes are not.
- A paraphrased later question retrieves the exemplar for the same tenant.
- Other tenants cannot retrieve it.
- Superseding an exemplar preserves historical citations.

## Done when

FR11's semantic-retrieval success criterion passes and approved-edit reuse remains auditable, tenant-scoped evidence rather than a hidden learning loop.
