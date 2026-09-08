# Phase 23 — Contradiction, freshness, and precedent checks

**Feature branch:** `codex/feature-23-verifier-risk-checks`  
**Depends on:** Phase 22  
**Traceability:** `specs/07-verification.md`, `specs/11-evaluation-and-baselines.md`; FR7, H3

## Goal

Extend verification to the hard-negative cases most likely to produce polished but unsafe answers.

## Implementation

- Check cited and nearby evidence for contradictions.
- Compare validity windows to the current evaluation time and flag stale/future evidence.
- Compare claims with similar prior approved answers from the same tenant.
- Return explicit contradiction/freshness/precedent flags without rewriting the answer.

## Unit tests

- Removed evidence, contradictory versions, stale evidence, future-dated evidence, and conflicting approved precedent.
- Time-boundary cases with a fixed clock.
- Similar precedent from another tenant is never visible.
- Multiple simultaneous risks remain machine-readable.

## Done when

All required verification dimensions are represented in `VerificationResult`, and injected hard negatives can be scored for the FR7 detection target.
