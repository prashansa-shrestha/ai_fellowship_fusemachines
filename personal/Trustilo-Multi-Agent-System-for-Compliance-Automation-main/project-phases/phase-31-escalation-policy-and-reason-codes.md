# Phase 31 — Escalation policy and reason codes

**Feature branch:** `codex/feature-31-escalation-policy`  
**Depends on:** Phase 30  
**Traceability:** `specs/08-escalation-and-review.md`; FR8, NFR9, H5

## Goal

Convert retrieval and verification signals into a deterministic auto-finalize/escalate decision with complete explanations.

## Implementation

- Define versioned reason codes for missing evidence, contradiction, stale evidence, low verifier support, and novelty.
- Combine retrieval-side and verifier-side features; keep generator-only confidence available solely as an H5 baseline.
- Read all thresholds from frozen `ExperimentConfig`.
- Require non-empty reason codes and a human-readable explanation for every escalation.

## Unit tests

- One fixture per reason code plus multiple simultaneous reasons.
- Threshold boundary, abstention, and missing-signal behavior.
- Auto-finalize is blocked by mandatory safety flags.
- Generator self-confidence alone cannot override composite risk.

## Done when

Every decision is deterministic, versioned, explainable, and suitable for threshold calibration without untracked special cases.
