# Phase 02 — Canonical schemas and invariants

**Feature branch:** `codex/feature-02-canonical-schemas`  
**Depends on:** Phase 01  
**Traceability:** `specs/02-data-model.md`; FR3, FR5, FR6, NFR9

## Goal

Make `src/trustilo/common/schemas.py` the complete, validated contract shared by every pipeline stage.

## Implementation

- Complete the core entities, answer-status enum, pipeline state, version metadata, retrieval scores, and experiment config.
- Enforce required evidence identity and tenant fields.
- Reject uncited claims unless the parent answer is an explicit abstention.
- Require machine-readable and human-readable reasons on escalations.
- Use opaque string IDs and keep the schema spec synchronized with any necessary clarification.

## Unit tests

- Valid construction and serialization for every entity.
- Failure cases for missing `tenant_id`, document/version/source metadata, invalid answer status, uncited claims, and empty escalation reasons.
- Round-trip JSON tests for persisted contracts.

## Done when

All stage contracts can be expressed using canonical models and invalid safety-critical states fail at validation time rather than later in the pipeline.
