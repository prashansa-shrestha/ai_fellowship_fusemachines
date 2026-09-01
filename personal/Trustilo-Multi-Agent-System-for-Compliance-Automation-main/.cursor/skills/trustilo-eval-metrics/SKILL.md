---
name: trustilo-eval-metrics
description: Computes Trustilo's standard evaluation metrics (retrieval Recall@k/MRR, claim-support precision/recall, unsupported-claim rate, escalation precision/recall/F1, calibration/Brier score, cost & latency summaries) exactly as defined in specs/11-evaluation-and-baselines.md. Use whenever comparing baselines B0/B1/B2/P, running an ablation, or reporting benchmark numbers — instead of re-deriving a formula inline.
---

# Trustilo Evaluation Metrics

Every metric Trustilo reports has one implementation, here, so B0 /
B1 / B2 / P and every ablation in `specs/11-evaluation-and-baselines.md`
are scored identically. If you find yourself writing `precision =
...` inline somewhere else in the codebase for one of the metrics
below, stop and call this skill's functions instead.

## When to use

- After running a baseline or ablation (see `/run-baseline`).
- Whenever a PR touches retrieval, drafting, verification, or
  escalation and you want to know whether quality moved.
- Before writing an ablation report (`/write-ablation-report`) or
  updating `specs/14-requirements-traceability.md` to `verified`.

## Input format

`scripts/run_eval.py` expects a JSONL file, one record per evaluated
question, with the fields documented at the top of `scripts/metrics.py`
(`EvalRecord`). At minimum: retrieved vs. gold evidence chunk ids,
per-claim support labels, the escalation decision vs. gold "needs
review" label, a confidence score, and latency/cost figures. Build
this JSONL from `src/trustilo/evaluation/` — the skill only consumes
it, it doesn't run the pipeline itself.

## Usage

```bash
python .cursor/skills/trustilo-eval-metrics/scripts/run_eval.py \
    --input path/to/eval_records.jsonl \
    --baseline P \
    --out tests/eval/reports/P_dev_run.json
```

This prints a metrics table to stdout and writes the same data as JSON
to `--out`. Run it once per baseline you're comparing, then diff the
JSON outputs (or hand them to `/write-ablation-report`).

## What each function computes, and where it maps in the paper

See `references/metric-definitions.md` for exact formulas and the
row of the paper's Evaluation Metrics table each one corresponds to.
Quick index into `scripts/metrics.py`:

| Function | Metric area |
|---|---|
| `recall_at_k` | Retrieval Recall@k |
| `mean_reciprocal_rank` | Retrieval MRR |
| `claim_support_precision_recall` | Groundedness |
| `unsupported_claim_rate` | Groundedness |
| `escalation_precision_recall_f1` | Verification *and* Escalation (same function — label column differs) |
| `brier_score` / `reliability_bins` | Calibration |
| `cost_latency_summary` | Operations |

## Rules for extending this skill

- New metric → add the function to `scripts/metrics.py` with a
  docstring citing the exact paper/spec line it implements, add a row
  to `references/metric-definitions.md`, and add it to the table
  above. Don't add a metric no spec section asks for.
- Keep `scripts/metrics.py` dependency-free (standard library only) so
  it runs in any environment without an install step — this is
  deliberate, not an oversight.
- Never round or truncate inside a metric function — return full
  precision and let the report layer decide display formatting, so
  small deltas between ablations aren't hidden by rounding.
