# Phase 11 — PDF ingestion and confidence flags

**Feature branch:** `codex/feature-11-pdf-intake`  
**Depends on:** Phase 10  
**Traceability:** `specs/04-intake-classification.md`; FR1

## Goal

Extract questions from text-native PDFs and surface uncertain table/scan extraction explicitly.

## Implementation

- Parse text and tables with deterministic page/order provenance.
- Detect pages that likely require OCR and place OCR behind an optional adapter.
- Attach extraction-confidence flags and diagnostics per question.
- Never silently infer broken row alignment or let parse failures appear as later retrieval misses.

## Unit tests

- Text-native, multi-column, table-based, and repeated-header PDFs.
- Scanned-page detection with the OCR adapter mocked.
- Page/order preservation and deterministic normalization.
- Corrupt/password-protected files and low-confidence extraction behavior.

## Done when

PDF fixtures are included in the fixed FR1 corpus, uncertain extraction is machine-visible, and the aggregate extraction target can be measured across PDF, XLSX/CSV, and text.
