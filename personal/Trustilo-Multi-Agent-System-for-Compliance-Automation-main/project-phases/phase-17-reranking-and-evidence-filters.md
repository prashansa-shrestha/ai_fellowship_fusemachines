# Phase 17 — Re-ranking and evidence filters

**Feature branch:** `codex/feature-17-reranking-filters`  
**Depends on:** Phase 16  
**Traceability:** `specs/05-retrieval.md`; FR4, NFR2

## Goal

Add optional re-ranking, version/freshness controls, and the revised-query entry point without changing the retrieval contract.

## Implementation

- Re-rank a configurable fused top-N before final top-k truncation.
- Pass original or explicitly revised query as separate inputs and retain both for audit.
- Exclude superseded evidence by default while surfacing validity metadata.
- Add hybrid-with-rerank and prior-approved-Q/A inclusion toggles to `ExperimentConfig`.

## Unit tests

- Re-ranker disabled/enabled, malformed output, ties, and fallback behavior.
- Original versus revised query propagation.
- Active, superseded, expired, and future-dated evidence cases.
- Tenant predicates remain enforced on every configurable path.

## Done when

All required retrieval strategies are config-driven, return consistent metadata, and remain safe under failure or optional-component disablement.
