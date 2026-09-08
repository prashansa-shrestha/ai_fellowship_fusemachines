# AGENTS.md — tests/eval

The baseline/ablation harness and its fixtures. Full spec:
`../../specs/11-evaluation-and-baselines.md`.

- Reports land in `tests/eval/reports/` as dated JSON/markdown files
  (see `.cursor/commands/run-baseline.md` and
  `.cursor/commands/write-ablation-report.md`) — `.gitignore` excludes
  the JSON by default so the repo doesn't accumulate run artifacts;
  commit a report explicitly (`git add -f`) if it should be preserved,
  e.g. the final held-out test run for submission.
- Dev-split and test-split fixtures live under clearly separate paths
  (`data/benchmark_dev/`, `data/benchmark_test/`) — don't introduce a
  single path with a "split" flag that could be passed incorrectly.
- The `eval-runner` subagent (`.cursor/agents/eval-runner.md`) is
  scoped to only write within this directory — keep it that way when
  extending the harness.
