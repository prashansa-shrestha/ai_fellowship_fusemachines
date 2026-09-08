# Phase 25 — Core RAG integration checkpoint

**Feature branch:** `codex/feature-25-core-rag-integration`  
**Depends on:** Phases 19–24  
**Traceability:** `specs/05-retrieval.md` through `specs/07-verification.md`; FR4–FR7, NFR1, H3

## Goal

Exercise retrieval, drafting, citation resolution, verification, and one-shot query revision as a single safety-focused flow.

## Integration tests

- Supported evidence produces cited claims that pass independent verification.
- Missing evidence produces an abstention, not a fabricated answer.
- A first-pass retrieval miss is recovered by one revised query and fresh draft.
- Contradictory, stale, fabricated-citation, and prompt-injection fixtures are flagged.
- A second requery is impossible and all calls retain tenant/config/version metadata.
- Measure claim-support precision and verifier detection on development hard negatives.

## Done when

The core RAG path satisfies its structural safety invariants and reports honest dev-set results for FR4–FR7; orchestration state transitions are intentionally added in the following phases.
