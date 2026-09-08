# Phase 05 — Foundation integration checkpoint

**Feature branch:** `codex/feature-05-foundation-integration`  
**Depends on:** Phases 01–04  
**Traceability:** `specs/01-architecture.md` through `specs/03-orchestrator.md`; NFR2, NFR3, NFR5, NFR7

## Goal

Prove that schemas, configuration, provider abstraction, and persistence agree before feature stages build on them.

## Integration tests

- Create a question, evidence document/chunk, answer, verification result, and audit event under one `config_id`; persist and reload the entire graph.
- Attempt cross-tenant lookups for every repository and assert no result escapes the storage boundary.
- Replay a duplicate stage idempotency key and confirm the existing result is returned without a second provider call.
- Resolve every stored foreign ID and verify JSON serialization remains stable.

## Done when

The foundation integration suite passes with the in-memory repositories and, where available, PostgreSQL. No production feature is added in this checkpoint; failures are fixed at the owning contract before Phase 06 begins.
