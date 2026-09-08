# Phase 16 — Hybrid fusion

**Feature branch:** `codex/feature-16-hybrid-fusion`  
**Depends on:** Phases 14–15  
**Traceability:** `specs/05-retrieval.md`, `specs/11-evaluation-and-baselines.md`; FR4, H2

## Goal

Combine dense and sparse rankings reproducibly and expose all retrieval ablation modes through configuration.

## Implementation

- Implement reciprocal-rank fusion or a documented weighted-score method.
- Deduplicate chunks, retain component scores/ranks, and apply deterministic tie-breaking.
- Support dense-only, sparse-only, and hybrid-no-rerank without editing source code.
- Log strategy and parameters under the current `config_id`.

## Tests

- Unit tests for fusion math, missing results from one retriever, duplicates, ties, and top-k.
- Property tests that ordering is deterministic for identical inputs.
- Evaluation smoke run calculating Recall@5/10 and MRR with the approved metric utilities.

## Done when

Hybrid retrieval is directly comparable with both component strategies and produces enough provenance to explain every fused rank.
