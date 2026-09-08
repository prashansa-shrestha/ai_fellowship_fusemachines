# AGENTS.md — evaluation

Owns: running B0/B1/B2/P and the seven required ablations, producing
per-question JSONL that `.cursor/skills/trustilo-eval-metrics` turns
into a metrics report. Full spec:
`../../../specs/11-evaluation-and-baselines.md`.

- This package computes/collects the raw per-question fields (gold
  evidence ids, claim support labels, escalation flags, confidence,
  latency, cost) — it does NOT recompute Recall@k, precision/recall,
  Brier score, etc. itself. Call
  `.cursor/skills/trustilo-eval-metrics/scripts/metrics.py` for that,
  so every baseline is scored identically.
- Never read from or write to the frozen held-out test set except
  during an explicitly-confirmed final test run — see
  `../../../.cursor/rules/eval-benchmark-integrity.mdc`. Keep dev and
  test data under clearly separate paths, not a flag that could be
  forgotten.
- Every run records its `ExperimentConfig.config_id` alongside results
  so a metric change is attributable to a specific component swap.
- RAGAS/ARES-style judge-model metrics (context relevance, answer
  relevance) are a deliberate v2 addition here, not required for the
  MVP loop — see `.cursor/skills/trustilo-eval-metrics/references/metric-definitions.md`.
