# Phase 09 — XLSX questionnaire ingestion

**Feature branch:** `codex/feature-09-xlsx-intake`  
**Depends on:** Phase 08  
**Traceability:** `specs/04-intake-classification.md`, `specs/10-export-audit-feedback.md`; FR1, FR10

## Goal

Parse spreadsheet questionnaires while retaining enough coordinates to write each answer back to its exact source location.

## Implementation

- Detect configured question, identifier, section, and answer columns across sheets.
- Preserve workbook sheet, source row, question column, and target answer column as structured provenance.
- Handle merged headers and empty/decorative rows conservatively.
- Flag ambiguous layouts for review instead of guessing alignment.

## Unit tests

- Single- and multi-sheet workbooks, reordered columns, formulas, merged headers, hidden rows, and blank cells.
- Exact coordinate preservation for every extracted question.
- Unsupported/encrypted workbook failure behavior.
- Workbook bytes remain unchanged during ingestion.

## Done when

Curated XLSX fixtures parse deterministically and each question carries the coordinates Phase 36 will need for lossless answer placement.
