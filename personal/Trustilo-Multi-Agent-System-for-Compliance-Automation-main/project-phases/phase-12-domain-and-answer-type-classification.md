# Phase 12 — Domain and answer-type classification

**Feature branch:** `codex/feature-12-question-classification`  
**Depends on:** Phases 03 and 11  
**Traceability:** `specs/04-intake-classification.md`, `specs/11-evaluation-and-baselines.md`; FR2

## Goal

Classify normalized questions by domain, question type, and expected answer type using a reproducible, configurable classifier.

## Implementation

- Define the CAIQ-aligned domain taxonomy and supported answer types.
- Preserve the existing transparent rules as a deterministic baseline; add provider-backed classification only behind the common LLM interface if needed.
- Store classifier/model version and confidence with the result.
- Keep the SME-labelled development/test fixtures separate and immutable during evaluation.

## Tests

- Unit tests for known examples, unknown labels, malformed model output, and deterministic fallback.
- Evaluation script for per-class results and macro-F1.
- Verify no classification call can change extraction provenance.

## Done when

The classifier produces valid labels for all curated questions and reports FR2's ≥85% macro-F1 target or an explicitly documented alternative metric.
