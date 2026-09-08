# 11 — Evaluation & Baselines

Status: living document. Source: `report/main.tex` §III.F, §V.B–V.C,
§VI. This is the spec `.cursor/skills/trustilo-eval-metrics` implements
and `.cursor/agents/eval-runner.md` runs against.

## Baselines — always compare against all of these, not just P

| ID | Name | Description |
|---|---|---|
| B0 | Direct LLM | Question only, no external evidence. Intentionally weak — measures the value of retrieval and exposes unsupported-answer behavior. |
| B1 | Single-agent RAG | One retriever + one answer-generation call using retrieved evidence; no independent verification agent. |
| B2 | RAG + verifier | B1 + a separate evidence-support/contradiction check, but no multi-agent routing or human escalation logic. |
| P | Trustilo (proposed) | Orchestrated classification + hybrid retrieval + grounded drafting + verification + confidence/escalation + human review. |
| Human reference | SME-written/approved answers | Reference point, not a machine baseline — also used for manual completion time comparison (H4). |

Every reported metric must be computed identically across B0/B1/B2/P
on the **same held-out question set** — a metric computed differently
per baseline (different prompt, different sample) is not a valid
comparison and defeats the point of having baselines at all.

## Metrics (mirrors the paper's Evaluation Metrics table)

| Area | Metric | Skill function |
|---|---|---|
| Ingestion | question extraction precision/recall or row accuracy | — (see `specs/04-intake-classification.md`, tracked separately) |
| Retrieval | Recall@5/10, MRR | `metrics.recall_at_k`, `metrics.mean_reciprocal_rank` |
| Answer quality | SME correctness / substantive correction rate | manual, from `ReviewTask` outcomes |
| Groundedness | claim-support precision/recall; unsupported-claim rate | `metrics.claim_support_precision_recall`, `metrics.unsupported_claim_rate` |
| RAG quality | context relevance, answer faithfulness, answer relevance | RAGAS/ARES-inspired — implement as an extension to the skill once a judge model is chosen; don't block MVP on this |
| Verification | precision/recall/F1 on injected unsupported/contradictory cases | `metrics.escalation_precision_recall_f1` (same function, different label column) |
| Escalation | precision, recall, F1; workload reduction | `metrics.escalation_precision_recall_f1` |
| Calibration | Brier score; reliability/ECE | `metrics.brier_score`, `metrics.reliability_bins` |
| Operations | median/P95 latency, tokens/cost | `metrics.cost_latency_summary` |
| Human factors | reviewer time/question; accept/edit/reject rates | manual, from `ReviewTask` + timing logs |

Full formulas and paper cross-references:
`.cursor/skills/trustilo-eval-metrics/references/metric-definitions.md`.
**Use the skill's functions, don't hand-roll these formulas inline** —
see `.cursor/rules/eval-benchmark-integrity.mdc` for why that matters.

## Ablation plan — required, not optional, for the final report

- dense-only vs. sparse-only vs. hybrid retrieval
- with vs. without re-ranking
- single drafting call vs. drafting + independent verifier
- verifier without query revision vs. verifier with one re-retrieval cycle
- confidence from generator only vs. composite retrieval+verifier confidence (this is H5 — see `specs/07-verification.md`)
- with vs. without previously-approved Q/A retrieval (FR11's effect)
- optional self-consistency sampling only on borderline cases

Each ablation is a distinct `ExperimentConfig`, run through the same
harness as the baselines, on the same dev/test splits.

## Test protocol

- Stratify the final benchmark by: question domain, duplicate/novel
  status, evidence sufficiency, and deliberate failure type (see hard
  negatives below).
- Tune prompts/models/retrieval/thresholds **only** on the development
  split.
- **Freeze the test set and the thresholds before the held-out test
  run.** No further tuning after that point, full stop.
- At least a subset of test cases gets independently reviewed twice,
  or adjudicated on disagreement — security wording is often ambiguous
  enough that a single label isn't reliable.

## Hard negatives (what makes B0 vs. P differences meaningful)

Per the Data Acquisition Methods: deliberately construct cases with
evidence removed, contradictory evidence versions inserted, and stale
evidence substituted. These specifically stress Verification and
Escalation — without them, a system that never abstains can still look
good on easy questions.

## Error taxonomy — assign exactly one primary cause per failed answer

```
ingestion_parsing_error | retrieval_miss | retrieved_evidence_insufficient
| evidence_stale | generator_ignored_evidence | unsupported_synthesis
| contradiction_missed | verifier_false_positive | verifier_false_negative
| escalation_threshold_error | human_label_ambiguity
```

This turns the final report from a single score into an engineering
roadmap — every automated eval run should tag failures with one of
these, not just report an aggregate pass rate.

## Interfaces

```
eval.run_baseline(config: ExperimentConfig, split: Literal["dev","test"]) -> list[EvalRecord]
eval.compute_metrics(records: list[EvalRecord]) -> MetricsReport   # delegates to the skill
eval.tag_error(answer: Answer, gold: GoldLabel) -> ErrorCategory
```
