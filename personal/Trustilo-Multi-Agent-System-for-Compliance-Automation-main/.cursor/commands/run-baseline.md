Run one of the Trustilo baselines (B0, B1, B2, or P — ask which if not
specified) against the current development split and report metrics.

1. Read `specs/11-evaluation-and-baselines.md` for the baseline
   definitions and which `ExperimentConfig` fields distinguish them.
2. Confirm the harness in `src/trustilo/evaluation/` and
   `tests/eval/` is pointed at the **development** split, not the
   frozen test set, unless the user has explicitly said this is the
   final held-out test run (see `.cursor/rules/eval-benchmark-integrity.mdc`).
3. Run the baseline and compute metrics using
   `.cursor/skills/trustilo-eval-metrics` — don't recompute formulas
   inline.
4. Report the metrics table for this run, and if a previous run for
   the same baseline exists, show the delta.
5. Tag any failed answers with an error-taxonomy category from
   `specs/11-evaluation-and-baselines.md`.
6. Do not adjust escalation thresholds as part of this command unless
   explicitly asked — threshold calibration is a separate, deliberate
   step that must stay on the dev split only.
