# Phase 22 — Independent support verification

**Feature branch:** `codex/feature-22-support-verification`  
**Depends on:** Phase 21  
**Traceability:** `specs/07-verification.md`; FR7

## Goal

Independently assess whether each claim is entailed by its cited evidence without using the drafter's reasoning or self-confidence.

## Implementation

- Give the verifier only canonical claims, cited evidence text, and necessary metadata.
- Produce per-claim support outcomes plus an aggregate support score.
- Use the common provider abstraction with a deterministic verifier/test double.
- Validate structured verifier output and stamp verifier/config versions.

## Unit tests

- Fully supported, partially supported, unsupported, and citation/text mismatch cases.
- Multi-claim aggregation and threshold boundaries.
- Drafter confidence or hidden reasoning cannot enter the verifier request.
- Malformed provider output fails closed.

## Done when

Verification re-derives support from evidence and provides reproducible signals that escalation can consume independently of generation.
