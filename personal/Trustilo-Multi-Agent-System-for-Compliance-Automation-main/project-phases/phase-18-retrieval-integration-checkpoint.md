# Phase 18 — Retrieval integration checkpoint

**Feature branch:** `codex/feature-18-retrieval-integration`  
**Depends on:** Phases 14–17  
**Traceability:** `specs/05-retrieval.md`, `specs/11-evaluation-and-baselines.md`; FR4, NFR2, H2

## Goal

Validate the complete evidence-ingestion-to-retrieval path and establish the H2 measurement baseline.

## Integration and evaluation tests

- Ingest and chunk a synthetic two-tenant corpus, build dense/sparse indexes, and query all configured modes.
- Assert zero cross-tenant rows leave the database for every mode, including re-ranking and revised queries.
- Run dense-only, sparse-only, hybrid-no-rerank, and hybrid-with-rerank on the same gold mappings.
- Compute Recall@5/10 and MRR using the project metric skill; report whether Recall@10 reaches 90% without tuning on the held-out split.
- Confirm stale/superseded filtering and audit metadata end to end.

## Done when

The retrieval stack passes adversarial isolation tests and produces a reproducible dev-set comparison suitable for H2, with any target gap documented rather than hidden.
