Produce a short ablation report from existing baseline/ablation run
results (do not launch new runs unless the relevant results are
missing — ask before running anything expensive).

Structure the report as:

1. One line stating which ablation this covers (pick from the seven in
   `specs/11-evaluation-and-baselines.md` if not specified).
2. A results table: configuration vs. the relevant metric(s) from
   `.cursor/skills/trustilo-eval-metrics`, with deltas.
3. A short interpretation grounded only in the numbers actually
   produced — don't claim a result is "significant" or "confirms H2/H5"
   etc. without the numbers supporting it; note when a difference is
   within noise given the sample size.
4. Which error-taxonomy categories shifted, if the data is available.
5. A one-line recommendation (keep/drop/investigate further).

Save the report under `tests/eval/reports/` as a dated markdown file
and mention it in the response — don't just print it inline and lose it.
