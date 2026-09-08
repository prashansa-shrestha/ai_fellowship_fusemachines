# `report/main.tex` structure notes

A map of the document as submitted, so edits land in the right place
without re-reading the whole file every time. Section numbers are
IEEEtran auto-numbering (Roman numerals) — don't hardcode "Section V"
in prose anywhere else, since inserting a new top-level section would
shift everything after it.

Compile with `pdflatex` (the file header says so explicitly); run it
twice for the bibliography/cross-references to resolve.

## Document class & preamble

`\documentclass[11pt,journal,onecolumn]{IEEEtran}`. Custom colors are
named semantically after pipeline stages (`orchcolor`, `intakecolor`,
`retrievalcolor`, `draftcolor`, `verifycolor`, `mapcolor`,
`escalatecolor`, `learncolor`, `storecolor`, `outputcolor`,
`borderline`) — reuse these if adding new diagram elements rather than
introducing new colors, to keep the palette restrained as the header
comment intends.

## Section map

| # | Title | Contains |
|---|---|---|
| I | Project Context | Summary, Problem Statement, Goals, Application Areas, Justification, **Scope** (MVP in/out — mirrors `specs/00-overview-and-mvp-scope.md`), Limitations, Assumptions, Team Member Details table |
| II | Requirements | Expected Inputs/Outputs, End-User/Stakeholder Requirements table, **Functional Requirements table (FR1–FR12)**, **Non-Functional Requirements table (NFR1–NFR9)** — this is what `specs/14-requirements-traceability.md` mirrors |
| III | Data Collection, Data Sources, and Benchmarking | Data Identification, Data Sources table, Acquisition Methods, Collection Challenges, **Baseline Models (B0/B1/B2/P/Human)**, Resources Required |
| IV | Literature Review (`\label{sec:litreview}`) | Research Question, Sub-Problems, General Review, Datasets table, Common Models, Major Issues, **9 detailed paper reviews** (subsubsections "Paper 1" … "Paper 9"), **Literature Review Matrix** (landscape `longtable`, `\label{tab:litmatrix}`), Synthesis/Research Gap |
| V | Project Solution Proposal | **Hypotheses H1–H5**, Experiment and Development Plan, Ablation Plan, **Tentative Architecture** (TikZ figure, `\label{fig:architecture}`), Agent Responsibilities, Requirement Updates from the Lit Review |
| VI | Evaluation Plan | Metrics table, Test Protocol, Error Taxonomy |
| VII | Security, Auditability, and Data Governance | — |
| VIII | Proposed Technology Stack | Candidate stack table |
| IX | Timeline (`\label{sec:timeline}`) | `pgfgantt` chart, `\label{fig:gantt}`, 24-week schedule |
| X | Expected Research Contributions and Deliverables | — |
| XI | Conclusion | — |
| Appendix A | Template Coverage Checklist | Maps each AIF template requirement to its section in this report |
| — | Bibliography | `\begin{thebibliography}{99}`, 14 `\bibitem`s, keys like `lewis2020rag`, `he2024covrag`, `csa2026ccm` — cited with `\cite{}` throughout |

## Where results will actually land as the project progresses

- **§III.E baseline table / §V.B experiment plan** → fill with real
  numbers once `tests/eval/reports/` has B0/B1/B2/P runs. Cross-check
  against `specs/11-evaluation-and-baselines.md`.
- **§V.D Fig. `fig:architecture`** → the TikZ diagram mirrors
  `specs/01-architecture.md`'s mermaid diagram conceptually (same
  nodes/edges, different rendering). If the architecture spec changes
  in a way that affects the picture, update both, and say so in the
  edit rather than silently letting them diverge.
- **§VI.A Metrics table** → once real metrics exist, this table is
  where the actual (not just planned) numbers go, sourced from
  `.cursor/skills/trustilo-eval-metrics` reports.
- **§IX Fig. `fig:gantt`** → compare against
  `specs/roadmap-24-week.md`'s checkboxes near submission time; update
  the schedule only if the actual timeline diverged from the plan,
  and note why.
- **Appendix A checklist** → sanity-check this still points to correct
  section labels any time a section is added or reordered.

## Things that will break the build if edited carelessly

- `tabularx` column specs (e.g. `L{0.29\textwidth}Y L{0.10\textwidth} Y`)
  must match the number of `&`-separated cells in every row of that
  table — adding a column means updating every row, not just the
  header.
- The `landscape` environment around the Literature Review Matrix
  needs `pdflscape` (already loaded) — don't wrap additional content
  in it without checking page-break behavior in a full recompile.
- `\cite{}` keys must exist in `thebibliography`; a typo'd key
  compiles with a warning (undefined reference), not an error — always
  grep the bibliography for a key before using it in a new `\cite{}`.
- `\label{}`/`\ref{}` pairs (`fig:architecture`, `fig:gantt`,
  `tab:litmatrix`, `sec:litreview`, `sec:timeline`) — renaming a label
  silently breaks every `\ref{}` to it until the next full recompile
  surfaces the warning.
