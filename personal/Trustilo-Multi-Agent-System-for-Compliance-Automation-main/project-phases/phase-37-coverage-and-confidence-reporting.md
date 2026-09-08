# Phase 37 — Coverage and confidence reporting

**Feature branch:** `codex/feature-37-coverage-report`  
**Depends on:** Phase 36  
**Traceability:** `specs/10-export-audit-feedback.md`; FR10, NFR3

## Goal

Produce a separate stakeholder-facing report that summarizes coverage and risk without exposing confidential raw logs.

## Implementation

- Report auto-finalized, escalated, reviewer-resolved, abstained, and unresolved counts.
- Include confidence distribution and per-domain coverage using the frozen decision/config version.
- Link answer summaries to reconstructable lineage identifiers.
- Define deterministic JSON plus one human-readable representation.

## Unit tests

- Aggregation across mixed statuses, domains, and confidence bins.
- Empty questionnaire, missing classification, and partially resolved cases.
- Counts reconcile exactly with exported answers.
- Tenant scoping and sensitive-field exclusion.

## Done when

Stakeholders can understand questionnaire coverage and risk from the report, and every reported total can be reconciled with tenant-scoped finalized pipeline records.
