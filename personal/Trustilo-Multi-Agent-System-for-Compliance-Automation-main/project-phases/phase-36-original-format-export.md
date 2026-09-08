# Phase 36 — Original-format export

**Feature branch:** `codex/feature-36-original-format-export`  
**Depends on:** Phases 09 and 35  
**Traceability:** `specs/10-export-audit-feedback.md`; FR10

## Goal

Write finalized answers back into supported questionnaire formats without question/answer misalignment.

## Implementation

- Implement export dispatch by original source format.
- For XLSX, use preserved sheet/row/column coordinates and retain unrelated workbook content and formatting where practical.
- Define safe text/CSV outputs and explicit behavior for PDF, which may require a separate report rather than direct mutation.
- Export only authoritative finalized answers and represent unresolved items clearly.

## Tests

- XLSX round trip with multi-sheet, reordered, blank, and formula-containing workbooks.
- Assert every answer lands in its source question's target cell.
- Text/CSV order and encoding tests.
- Duplicate/missing coordinates, unresolved answers, and cross-tenant questionnaire access.

## Done when

The curated round-trip XLSX suite has zero answer/question misalignment and exports never substitute a non-final draft.
