# Phase 19 — Deterministic grounded drafting

**Feature branch:** `codex/feature-19-grounded-drafting-core`  
**Depends on:** Phase 18  
**Traceability:** `specs/06-drafting.md`; FR5, FR6, NFR1

## Goal

Harden the existing deterministic drafting behavior as the safest executable contract before adding model-backed generation.

## Implementation

- Accept only the question and selected evidence chunks.
- Produce atomic claims with exact chunk citations, or an explicit abstention with a reason.
- Treat evidence text as untrusted data, never instructions.
- Keep pass/escalate decisions outside drafting.
- Stamp answer, model/strategy, and experiment versions.

## Unit tests

- Supported answer, insufficient evidence, empty evidence, and conflicting evidence.
- Every non-abstained claim has at least one valid citation.
- Evidence instruction-injection text cannot change output schema or behavior.
- No claim can cite a chunk absent from the supplied evidence list.

## Done when

The deterministic path cannot emit an unsupported non-abstained claim and remains usable as a test oracle/fallback for later provider-backed drafting.
