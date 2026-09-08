# Phase 35 — Human-review integration checkpoint

**Feature branch:** `codex/feature-35-review-integration`  
**Depends on:** Phases 31–34  
**Traceability:** `specs/08-escalation-and-review.md`, `specs/09-reviewer-console.md`; FR8, FR9, NFR6, NFR9

## Goal

Prove that risky answers reach a reviewer with understandable evidence and that every human outcome becomes authoritative pipeline state.

## Integration and end-to-end tests

- Drive each escalation reason from pipeline fixture to review screen.
- Approve, edit, reject, and request evidence; reload the task and reconstruct its audit trail.
- Confirm edited citations remain valid and cross-tenant task access is denied.
- Simulate duplicate clicks/network retries and persist one decision.
- Run a small usability rehearsal measuring whether reviewers resolve tasks without raw logs; reserve the formal ≥90% measure for the pilot.

## Done when

Escalation-to-resolution works end to end, reasons are visible and machine-readable, and reviewer decisions are durable, auditable, and final.
