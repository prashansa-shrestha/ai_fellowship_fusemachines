# Phase 39 — Baselines, ablations, and error taxonomy

**Feature branch:** `codex/feature-39-evaluation-harness`  
**Depends on:** Phases 18, 25, 32, and 38  
**Traceability:** `specs/11-evaluation-and-baselines.md`; H1–H5, NFR8

## Goal

Create one reproducible evaluation harness for B0, B1, B2, Trustilo P, and every required ablation.

## Implementation

- Run every baseline on identical split records with immutable `ExperimentConfig` IDs.
- Support all specified retrieval, reranking, verification/requery, confidence, approved-edit, and optional borderline self-consistency ablations.
- Delegate metric calculations to the existing evaluation metric skill/functions.
- Assign exactly one primary error-taxonomy category to each failed answer.
- Record latency, cost, models, prompts/config versions, and run IDs.

## Tests

- Golden small-fixture outputs for each baseline and ablation.
- Same-sample enforcement, deterministic run resumption, and no test-set calibration.
- Metric adapter and error-category validation.
- Failed/partial run reporting without silent omission.

## Done when

A development-split run produces directly comparable, reproducible reports for B0/B1/B2/P and all required ablations; held-out execution remains reserved for Phase 40.
