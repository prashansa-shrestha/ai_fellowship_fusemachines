# Phase 13 — Duplicate and novelty detection

**Feature branch:** `codex/feature-13-duplicate-novelty`  
**Depends on:** Phase 12  
**Traceability:** `specs/04-intake-classification.md`, `specs/10-export-audit-feedback.md`; FR2, FR11

## Goal

Identify duplicate or semantically similar prior questions within the same tenant and expose novelty as a first-class classification output.

## Implementation

- Define exact-duplicate and semantic-similarity interfaces with configurable thresholds.
- Search only the current tenant's prior questions and approved precedents.
- Populate `duplicate_of`, similarity score, and novelty indicators without silently replacing the new question.
- Version the similarity configuration for later H5 and FR11 experiments.

## Unit tests

- Exact duplicates, paraphrases, unrelated questions, and threshold boundaries.
- Same text in two tenants never links across namespaces.
- No-candidate and stale/unapproved precedent behavior.
- Stable tie-breaking for equally similar candidates.

## Done when

Duplicate/novel status is deterministic, tenant-isolated, auditable, and usable by retrieval and escalation without a parallel hidden lookup.
