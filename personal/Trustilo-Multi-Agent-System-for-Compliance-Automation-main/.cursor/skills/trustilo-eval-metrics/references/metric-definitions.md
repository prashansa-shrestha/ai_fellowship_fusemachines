# Metric Definitions

Exact formulas behind `scripts/metrics.py`, cross-referenced to
`specs/11-evaluation-and-baselines.md` and the paper's Evaluation
Metrics table (`report/main.tex` §VI.A). If a formula here and the
docstring in `metrics.py` ever disagree, the code is the bug — file it,
don't just pick one silently.

## Retrieval

- **Recall@k** (`recall_at_k`, `mean_recall_at_k`): for one question,
  `|gold ∩ retrieved[:k]| / |gold|`. Reported as a macro-average across
  questions (each question weighted equally regardless of how many
  gold chunks it has). Questions with zero gold evidence are excluded,
  not scored as 0 or 1.
- **MRR** (`mean_reciprocal_rank`): mean of `1 / rank_of_first_hit`
  across questions; 0 for a question with no hit anywhere in the
  ranked list; questions with no gold evidence excluded.

## Groundedness

- **Claim-support precision**: `supported_claims / total_claims_made`,
  micro-averaged (summed numerators/denominators across the whole
  set, not averaged per-question ratios) so questions with more
  claims contribute proportionally more.
- **Claim-support recall**: `gold_claims_covered / total_gold_claims`,
  same micro-averaging.
- **Unsupported-claim rate**: `unsupported_claims / total_claims_made`
  — equivalent to `1 - precision` but computed independently; treat a
  divergence between the two as a sign one of them is being fed the
  wrong denominator somewhere upstream.
- Abstained answers (0 predicted claims) contribute 0 to the
  precision numerator *and* denominator — they don't inflate or
  deflate precision, which is why abstention is safe to use liberally
  without gaming this metric.

## Verification / Escalation (same function, two uses)

Standard binary precision/recall/F1 with "flagged" / "escalated" as
the positive class:
- `precision = tp / (tp + fp)`, `None` if no positives were predicted.
- `recall = tp / (tp + fn)`, `None` if gold has no positives.
- `f1 = 2PR / (P + R)`.

For **Verification**, positive = "verifier flagged as
unsupported/contradictory," gold = "this was a deliberately injected
hard negative" (`specs/11-evaluation-and-baselines.md`, Hard Negatives).
For **Escalation**, positive = "answer was escalated," gold = "SME
labeled this as needs review."

## Calibration

- **Brier score**: `mean((confidence_i - outcome_i)^2)`, outcome ∈
  {0,1}. Lower is better; 0 is perfect, 1 is worst-possible.
- **Reliability bins / ECE**: confidences bucketed into 10 equal-width
  bins `[0,0.1), [0.1,0.2), ..., [0.9,1.0]`; ECE = weighted average of
  `|mean_confidence - mean_outcome|` per bin, weighted by bin size.

## Operations

- **Median / P95 latency**: per stage and end-to-end, using the
  "inclusive" quantile method so P95 never reports a value larger than
  anything actually observed (matters most for small dev-split runs).
- **Cost**: summed and mean `cost_usd`, per stage and end-to-end.

## What this skill deliberately does NOT compute

- **RAGAS/ARES-style faithfulness/answer-relevance/context-relevance**
  judge scores — those require an LLM-as-judge call, which is a
  modeling decision (which judge model, which prompt) that belongs in
  `src/trustilo/evaluation/`, not hardcoded into a stdlib-only metrics
  skill. Once the team picks a judge approach, add a thin wrapper here
  that calls it and feeds the *result* into a metric function, the
  same way claim-support labels are supplied externally today.
- **Ingestion extraction accuracy** and **human-factors metrics**
  (reviewer time, accept/edit/reject rates) — these come directly from
  `ReviewTask` records and timing logs, not from model output judged
  against gold; compute them directly in
  `src/trustilo/evaluation/` rather than through this skill.
