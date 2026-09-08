Reconcile `report/main.tex` (the AIF submission) with current
implementation status, without breaking LaTeX structure.

Use the `aif-report-sync` skill for this — read its `SKILL.md` and
`references/latex-structure-notes.md` before editing anything.

1. Check `specs/14-requirements-traceability.md` and
   `specs/roadmap-24-week.md` for what's actually implemented/verified
   versus what `report/main.tex` currently claims (much of it is
   written in future/tentative tense, e.g. "tentative architecture",
   "proposed 24-week schedule" — that's expected pre-implementation,
   but should be tightened as real results land).
2. Propose specific, minimal edits — e.g. filling a results table cell
   with a real number, updating "proposed" to "implemented" language
   once something is actually done, adding a new `\bibitem` if a new
   source was cited. Do not restructure sections, renumber, or rewrite
   prose beyond what's needed to reflect reality.
3. Never fabricate a citation, DOI, dataset statistic, or metric value
   — every number that goes into the report must trace back to an
   actual benchmark run or the existing bibliography.
4. After edits, remind the user to recompile with `pdflatex` (twice,
   for cross-references) and check the bibliography still resolves.
5. Show a diff-style summary of what changed and why before assuming
   it should be applied wholesale.
