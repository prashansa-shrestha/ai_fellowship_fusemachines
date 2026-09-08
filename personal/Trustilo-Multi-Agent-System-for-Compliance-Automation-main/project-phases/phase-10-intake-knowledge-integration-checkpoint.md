# Phase 10 — Intake/knowledge integration checkpoint

**Feature branch:** `codex/feature-10-intake-knowledge-integration`  
**Depends on:** Phases 06–09  
**Traceability:** `specs/02-data-model.md`, `specs/04-intake-classification.md`; FR1, FR3, NFR2

## Goal

Verify that questionnaires and evidence can enter the same tenant-scoped system without losing provenance or contaminating one another.

## Integration tests

- Ingest representative text, CSV, and XLSX questionnaires plus versioned evidence for two tenants.
- Persist and reload question order, source coordinates, document/chunk metadata, and active-version state.
- Simulate a chunking/storage failure and verify atomic recovery without orphaned records.
- Measure extraction correctness on the frozen curated fixtures and report precision/recall or row accuracy.
- Assert instruction-like uploaded content cannot mutate parser, chunker, or configuration behavior.

## Done when

All supported non-PDF questionnaire paths and evidence ingestion work end to end, tenant isolation remains intact, and the measured FR1/FR3 status is recorded honestly in the pull request.
