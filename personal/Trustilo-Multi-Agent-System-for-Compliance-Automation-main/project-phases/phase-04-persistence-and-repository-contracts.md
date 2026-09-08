# Phase 04 — Persistence and repository contracts

**Feature branch:** `codex/feature-04-persistence-contracts`  
**Depends on:** Phases 02–03  
**Traceability:** `specs/02-data-model.md`, `specs/03-orchestrator.md`, `specs/12-security-and-governance.md`; NFR2, NFR3, NFR5

## Goal

Create explicit storage interfaces and database mappings for pipeline state, evidence metadata, stage results, review tasks, and append-only audit events.

## Implementation

- Add repository protocols with tenant-scoped method signatures.
- Define PostgreSQL migrations for canonical entities and pgvector readiness.
- Add uniqueness for idempotency keys `(question_id, stage_name, attempt)`.
- Make audit records append-only at the application and database boundary.
- Provide in-memory repositories for isolated unit tests.

## Unit tests

- Repository contract tests against the in-memory implementation.
- Duplicate idempotency-key handling and immutable-audit rejection.
- Tenant-scoped reads with two overlapping tenants.
- Migration upgrade test on an empty database when a test database is available.

## Done when

Storage callers cannot request unscoped evidence or state, and the persistence model can support retries, reconstruction, and later PostgreSQL retrieval work.
