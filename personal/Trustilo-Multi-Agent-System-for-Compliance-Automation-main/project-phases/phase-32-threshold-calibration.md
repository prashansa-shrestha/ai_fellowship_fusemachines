# Phase 32 — Threshold calibration

**Feature branch:** `codex/feature-32-threshold-calibration`  
**Depends on:** Phase 31  
**Traceability:** `specs/08-escalation-and-review.md`, `specs/11-evaluation-and-baselines.md`; FR8, H5

## Goal

Calibrate escalation thresholds on development data only and freeze them before held-out evaluation.

## Implementation

- Build a calibration command that can read only the development split path.
- Evaluate composite versus generator-only confidence with precision, recall, F1, Brier score, and reliability bins using approved metric functions.
- Select and serialize thresholds with their config ID and calibration provenance.
- Make the test split inaccessible to calibration by construction, not a caller flag.

## Tests

- Filesystem/config tests proving calibration cannot open the frozen test set.
- Deterministic threshold selection for fixed fixtures.
- Edge cases with no positives, tied scores, and invalid labels.
- Target report includes needs-review recall ≥90% and precision target ≥60%.

## Done when

Thresholds are reproducible, dev-calibrated, frozen, and ready for later held-out H5 evaluation without leakage.
