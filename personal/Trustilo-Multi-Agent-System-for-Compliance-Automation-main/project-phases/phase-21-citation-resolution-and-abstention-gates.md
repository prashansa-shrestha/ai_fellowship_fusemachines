# Phase 21 — Citation resolution and abstention gates

**Feature branch:** `codex/feature-21-citation-safety-gates`  
**Depends on:** Phase 20  
**Traceability:** `specs/02-data-model.md`, `specs/06-drafting.md`; FR5, FR6, NFR1, NFR2

## Goal

Enforce a final drafting-stage safety gate that resolves every citation and prevents unsupported answers from advancing.

## Implementation

- Resolve citations through a tenant-scoped repository before accepting a draft.
- Reject missing chunks, document/version mismatches, cross-tenant references, and claims unsupported by the supplied set.
- Normalize all insufficient-evidence paths into explicit abstentions with reason codes.
- Keep safety-gate results auditable and distinguish model failure from genuine evidence insufficiency.

## Unit tests

- Valid multi-claim/multi-citation answers.
- Missing, fabricated, duplicate, wrong-version, and cross-tenant citations.
- Empty claims with and without abstention.
- Repository failure and stale evidence behavior.

## Done when

One hundred percent of drafts eligible to advance have resolvable tenant-consistent citations, while uncertain cases become explicit abstentions or errors rather than plausible prose.
