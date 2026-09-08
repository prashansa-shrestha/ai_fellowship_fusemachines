# Phase 08 — Text and CSV questionnaire ingestion

**Feature branch:** `codex/feature-08-text-csv-intake`  
**Depends on:** Phase 05  
**Traceability:** `specs/04-intake-classification.md`; FR1

## Goal

Harden the existing deterministic text/CSV parser into a traceable questionnaire-ingestion contract.

## Implementation

- Preserve questionnaire order, source format, source row/line, provided identifiers, sections, raw text, and normalized text.
- Keep normalization deterministic and separate from classification or LLM calls.
- Emit explicit parse diagnostics and low-confidence flags instead of passing mangled questions onward.
- Define curated format fixtures without using confidential customer content.

## Unit tests

- UTF-8 text with headings, blank lines, multiline questions, and numbering.
- CSV quoting, embedded delimiters/newlines, missing cells, duplicate IDs, and unusual encodings.
- Stable normalization and source-position preservation.
- Malformed input produces a classified ingestion error.

## Done when

Text and CSV fixtures produce ordered, correctly aligned `Question` records and contribute to the FR1 extraction-correctness measurement.
