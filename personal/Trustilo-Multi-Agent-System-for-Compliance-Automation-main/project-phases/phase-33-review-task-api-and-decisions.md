# Phase 33 — Review-task API and decisions

**Feature branch:** `codex/feature-33-review-task-api`  
**Depends on:** Phases 28 and 32  
**Traceability:** `specs/08-escalation-and-review.md`, `specs/09-reviewer-console.md`; FR9, NFR9

## Goal

Expose tenant-scoped review tasks and persist authoritative human outcomes through the backend API.

## Implementation

- Create/list/get review tasks with question, claims, evidence, verification, and escalation details.
- Resolve with approve, edit, reject, or request-evidence actions.
- Validate corrected answers and citations; make reviewer decisions final and idempotent.
- Append reviewer audit events and route request-evidence to a distinct unresolved workflow state.

## Unit and API tests

- Authentication/tenant boundary tests for queue and detail endpoints.
- Every decision type, invalid transition, duplicate submission, and corrected-answer validation.
- Reviewer result overrides automation and appears in reconstructed lineage.
- Request-evidence is distinct from rejection.

## Done when

All reviewer decisions persist exactly once, cannot be second-guessed by automation, and are available for the console and export.
