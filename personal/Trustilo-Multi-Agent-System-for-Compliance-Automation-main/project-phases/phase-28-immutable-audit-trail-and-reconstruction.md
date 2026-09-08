# Phase 28 — Immutable audit trail and reconstruction

**Feature branch:** `codex/feature-28-audit-reconstruction`  
**Depends on:** Phase 27  
**Traceability:** `specs/03-orchestrator.md`, `specs/10-export-audit-feedback.md`; NFR3

## Goal

Record every material pipeline decision and reconstruct a finalized answer solely from its immutable event chain and referenced artifacts.

## Implementation

- Append events for stage entry/exit, retrieval queries/results, draft, verification, retry, escalation, and later reviewer decisions.
- Include actor, timestamps, tenant/question/config/version IDs, payload references, and ordered sequence.
- Implement `audit.reconstruct(answer_id)` with tenant-scoped resolution.
- Detect missing, duplicate, reordered, or cross-tenant references.

## Tests

- Unit tests for append-only behavior and deterministic event ordering.
- Reconstruct auto-finalized and escalated sample chains.
- Broken reference, altered event, and tenant mismatch failures.
- Integration test that every finalized fixture's IDs resolve.

## Done when

A finalized answer can be reproduced end to end without raw logs and audit history cannot be silently edited through application APIs.
