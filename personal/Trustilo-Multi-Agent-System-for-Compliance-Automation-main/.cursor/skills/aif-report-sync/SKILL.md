---
name: aif-report-sync
description: Keeps report/main.tex (the team's AIF requirement + literature review LaTeX submission) consistent with actual implementation progress and evaluation results as the 24-week project proceeds, without breaking LaTeX structure. Use when asked to update the report, fill in real results, add a citation, or reconcile the report with specs/ or specs/14-requirements-traceability.md.
---

# AIF Report Sync

`report/main.tex` is a real IEEEtran submission with a working
bibliography, tables, a TikZ architecture diagram, and a pgfgantt
timeline — not a draft to restructure freely. This skill is about
**surgical, evidence-based edits**: filling in a real number where the
report currently says "tentative" or "proposed," never rewriting
sections wholesale or inventing content.

## Before editing anything

1. Read `references/latex-structure-notes.md` for where things live
   (section names, labels, table structure) so edits land in the
   right place without re-deriving the document's structure from
   scratch each time.
2. Read `specs/14-requirements-traceability.md` and
   `specs/roadmap-24-week.md` to know what's actually
   implemented/verified versus still planned.
3. Diff what the report currently *claims* against what's actually
   true. Most of the report is intentionally written in
   proposal/future tense pre-implementation ("tentative architecture,"
   "proposed 24-week schedule") — that's correct as submitted and
   doesn't need "fixing" until there's a real result to report.

## Hard rules

- **Never fabricate a number.** A metric value, a dataset statistic, a
  DOI, an author name — every fact that goes into the report traces to
  either the existing bibliography or an actual benchmark run
  (`tests/eval/reports/`). If a number isn't available yet, leave the
  placeholder language alone rather than inventing something plausible.
- **Preserve LaTeX structure.** Don't touch `\begin{thebibliography}`
  formatting, don't change a `tabularx` column spec without checking
  every row still has the right cell count, don't rename a `\label{}`
  that other `\ref{}`/`\cite{}` calls depend on.
- **New citations get a real, verifiable source.** Follow the existing
  `\bibitem{key}` format; never invent a DOI or URL.
- **Additive, not destructive.** Prefer adding a sentence, filling a
  table cell, or appending a bibitem over rewriting an existing
  paragraph. If a claim is now simply wrong (e.g. an architecture
  decision changed), say what changed and why in the edit, don't
  silently overwrite it.

## Typical tasks

- **Filling the Evaluation Metrics / Literature Review results with
  real numbers** once `tests/eval/reports/` has actual runs — pull
  numbers from there, cite the run, never round differently than the
  source JSON.
- **Updating scope/timeline language** as `specs/roadmap-24-week.md`
  milestones get checked off — e.g. moving from "proposed 24-week
  schedule" to reporting actual progress against it, close to
  submission time.
- **Adding a bibitem** for a new source the team cites during
  implementation (e.g. a library's own documentation, if it's
  substantively informing a design decision worth citing).
- **Reconciling architecture drift** — if `specs/01-architecture.md`
  changed in a way that makes Fig. `fig:architecture` inaccurate, flag
  the specific TikZ nodes/edges that need updating rather than
  regenerating the whole diagram.

## After editing

Remind the user to recompile with `pdflatex` **twice** (bibliography
and cross-references need a second pass to resolve) and to check the
bibliography still resolves cleanly. This skill edits the `.tex`
source only — it does not compile or verify the PDF output.
