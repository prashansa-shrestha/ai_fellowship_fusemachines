Given a requirement ID (e.g. `FR7` or `NFR3`) provided after this
command, report and update its traceability status.

1. Look up the row in `specs/14-requirements-traceability.md` for the
   ID's requirement, spec file, and owning module.
2. Search the codebase (`src/trustilo/`, `tests/`) for the
   implementation and any tests that exercise its success criterion.
3. Report: is it implemented? Is there a test that actually checks the
   stated success criterion (not just that the code runs)? If the
   criterion needs a benchmark run (e.g. "Recall@10 ≥90%"), has that
   run happened, and with what result?
4. Propose an updated status (`not started` / `in progress` /
   `implemented` / `verified`) with one line of evidence, and apply
   the edit to `specs/14-requirements-traceability.md` if the user
   confirms it's accurate.
5. If the code contradicts the spec (not just "incomplete," but
   actually does something different from what's written), flag the
   discrepancy explicitly instead of silently updating status to match
   whichever one you find more plausible.
