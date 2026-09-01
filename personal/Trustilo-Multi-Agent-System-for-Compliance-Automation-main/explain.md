# Trustilo Phase 1: Intake and Classification

Phase 1 turns a small questionnaire into predictable `Question` records. It supports plain UTF-8 text,
UTF-8 CSV, and the active worksheet in an XLSX file. PDF is deliberately deferred and raises a clear
`NotImplementedError` instead of pretending that extraction succeeded.

## What happens

`parse(raw_file, source_format, tenant_id)` reads questions in source order. Plain text treats each non-empty
line as a question. CSV and XLSX find common question headers such as `Question` or `Question Text` without
regard to letter case, and retain an optional `Section` or `Category` column. Blank rows are skipped. CSV and
XLSX questions keep their physical row number, including the header row, so a later export can align an answer
with the original questionnaire.

The original question cell or line is stored in `raw_text`. A second value, `normalized_text`, collapses repeated
spaces, tabs, and line breaks without changing words or punctuation. Stable hash-based IDs are derived from the
tenant, format, exact input bytes, and question location. Parsing identical input twice therefore produces the
same IDs.

For example, `"Do you  require\tMFA?"` remains unchanged in `raw_text` and becomes
`"Do you require MFA?"` in `normalized_text`.

`classify(question)` returns a new `Question` instead of modifying the input. Small, readable keyword rules assign
a broad security domain such as `identity_and_access_management` and an expected answer shape such as `yes_no`,
`frequency`, `numeric`, or `free_text`. These rules make a useful supervisor demo because every result is easy to
trace, but they are a baseline—not a claim of production classification accuracy.

## Limits

- PDF parsing is not part of this checkpoint.
- XLSX parsing uses the active worksheet and expects headers in its first row.
- CSV and XLSX rows containing other data but no textual question raise an explicit error.
- Duplicate detection, novelty scoring, the complete CCM taxonomy, and benchmark accuracy validation remain
  future FR2 work. No success threshold is claimed yet, so FR1 and FR2 remain `in progress`.

## Verification

Run:

```bash
pytest -q tests/unit/test_schemas.py tests/unit/test_intake.py
ruff check src/trustilo/intake tests/unit/test_intake.py
```

The first command runs the canonical schema tests plus focused intake tests. The second checks the new Python code
for style and common mistakes. The tests cover normalization, deterministic IDs, CSV/XLSX source row preservation,
section retention, explicit PDF deferral, malformed-row errors, and non-mutating classification.
