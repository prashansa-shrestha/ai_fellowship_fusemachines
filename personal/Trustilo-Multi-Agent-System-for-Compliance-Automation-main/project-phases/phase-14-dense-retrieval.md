# Phase 14 — Dense retrieval

**Feature branch:** `codex/feature-14-dense-retrieval`  
**Depends on:** Phases 07 and 13  
**Traceability:** `specs/05-retrieval.md`, `specs/12-security-and-governance.md`; FR4, NFR2

## Goal

Implement the dense half of retrieval using pgvector while enforcing tenant and active-version filters inside the database query.

## Implementation

- Add embedding generation behind a provider-neutral interface and store embedding references/version metadata.
- Execute similarity search with `tenant_id` and active-version constraints in the SQL statement.
- Return ranked chunks with scores and full citation metadata.
- Expose dense-only mode through `ExperimentConfig`.

## Unit tests

- SQL/query-construction test proving the tenant predicate is present before execution.
- Ranking, top-k, empty corpus, embedding dimension, and provider failure cases.
- Adversarial overlapping content across two tenants.
- Superseded evidence exclusion and historical direct resolution.

## Done when

Dense-only retrieval is measurable on gold question-to-chunk mappings and returns zero cross-tenant candidates at the repository boundary.
