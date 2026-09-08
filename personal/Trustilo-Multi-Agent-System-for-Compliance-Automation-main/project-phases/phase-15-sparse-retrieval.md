# Phase 15 — Sparse retrieval

**Feature branch:** `codex/feature-15-sparse-retrieval`  
**Depends on:** Phase 14  
**Traceability:** `specs/05-retrieval.md`; FR4, NFR2

## Goal

Implement PostgreSQL full-text sparse retrieval as an independently evaluable strategy.

## Implementation

- Build and query tenant-scoped `tsvector` data with a documented language/normalization choice.
- Apply tenant and active-version constraints inside the database query.
- Return normalized lexical scores using the shared retrieval result contract.
- Expose sparse-only mode through `ExperimentConfig`.

## Unit tests

- Exact terms, phrases, punctuation, acronyms, stop words, and no-match queries.
- Stable ranking and top-k truncation.
- Cross-tenant overlapping content and superseded versions.
- Generated SQL contains all mandatory predicates.

## Done when

Sparse-only retrieval can run through the same interface and evaluation fixture as dense retrieval without code toggles or weakened isolation.
