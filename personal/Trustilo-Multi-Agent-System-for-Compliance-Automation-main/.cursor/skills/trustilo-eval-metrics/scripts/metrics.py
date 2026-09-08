"""Trustilo evaluation metrics.

Standard-library only, on purpose (see SKILL.md) — this must run in
any environment with no install step. Every function here implements
exactly one row of the Evaluation Metrics table in
specs/11-evaluation-and-baselines.md; the docstring says which one.

These functions consume *labels*, not raw model output — deciding
whether a claim is "supported" or an evidence chunk is "gold" is a
judgment call made upstream (by an SME, an entailment/judge model, or
a fixture builder for injected hard negatives). This module only
aggregates those labels into the metrics the paper asks for, so every
baseline (B0/B1/B2/P) is scored with exactly one formula per metric.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Retrieval: Recall@k, MRR
# --------------------------------------------------------------------------


def recall_at_k(gold_ids: list[str], retrieved_ids: list[str], k: int) -> float | None:
    """Recall@k for one question.

    Fraction of `gold_ids` that appear anywhere in the first `k`
    entries of `retrieved_ids` (a ranked list, best first).

    Returns None if `gold_ids` is empty (recall is undefined, not 0 —
    don't let an undefined case silently drag down an average).
    """
    if not gold_ids:
        return None
    top_k = set(retrieved_ids[:k])
    hits = sum(1 for g in gold_ids if g in top_k)
    return hits / len(gold_ids)


def mean_recall_at_k(
    per_question_gold: list[list[str]],
    per_question_retrieved: list[list[str]],
    k: int,
) -> float:
    """Macro-average Recall@k across questions (paper's "Recall@5/10").

    Questions with no gold evidence are skipped (see `recall_at_k`).
    """
    scores = [
        r
        for gold, retrieved in zip(per_question_gold, per_question_retrieved)
        if (r := recall_at_k(gold, retrieved, k)) is not None
    ]
    if not scores:
        raise ValueError("no question had non-empty gold evidence; cannot compute Recall@k")
    return sum(scores) / len(scores)


def reciprocal_rank(gold_ids: list[str], retrieved_ids: list[str]) -> float | None:
    """Reciprocal rank of the first relevant hit for one question.

    1/rank of the first item in `retrieved_ids` that is in `gold_ids`;
    0.0 if none of `retrieved_ids` is relevant. None if `gold_ids` is
    empty (undefined).
    """
    if not gold_ids:
        return None
    gold_set = set(gold_ids)
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in gold_set:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    per_question_gold: list[list[str]],
    per_question_retrieved: list[list[str]],
) -> float:
    """MRR across questions (paper's "Retrieval ... MRR")."""
    scores = [
        r
        for gold, retrieved in zip(per_question_gold, per_question_retrieved)
        if (r := reciprocal_rank(gold, retrieved)) is not None
    ]
    if not scores:
        raise ValueError("no question had non-empty gold evidence; cannot compute MRR")
    return sum(scores) / len(scores)


# --------------------------------------------------------------------------
# Groundedness: claim-support precision/recall, unsupported-claim rate
# --------------------------------------------------------------------------


@dataclass
class ClaimSupportRecord:
    """Per-question claim-support counts (labels from an SME/judge, not computed here).

    n_predicted_claims: total claims the system asserted (0 if the
        answer abstained — abstentions are excluded from the
        precision denominator, see `claim_support_precision_recall`).
    n_predicted_claims_supported: of those, how many are entailed by
        their cited evidence.
    n_gold_claims: how many claims a correct/reference answer should
        contain (from the gold answer for this question).
    n_gold_claims_covered: of the gold claims, how many are supported
        somewhere in the prediction (recall side).
    """

    question_id: str
    n_predicted_claims: int
    n_predicted_claims_supported: int
    n_gold_claims: int
    n_gold_claims_covered: int


@dataclass
class PrecisionRecall:
    precision: float | None
    recall: float | None
    n_claims: int
    n_supported: int
    n_gold_claims: int
    n_gold_covered: int

    @property
    def f1(self) -> float | None:
        if self.precision is None or self.recall is None or (self.precision + self.recall) == 0:
            return None
        return 2 * self.precision * self.recall / (self.precision + self.recall)


def claim_support_precision_recall(records: list[ClaimSupportRecord]) -> PrecisionRecall:
    """Claim-support precision/recall, micro-averaged across questions.

    precision = supported claims / total claims made (answers that
    abstained contribute 0/0 and are excluded from the denominator).
    recall = gold claims covered / total gold claims required.

    Maps to "Groundedness: claim-support precision/recall" in
    specs/11-evaluation-and-baselines.md.
    """
    n_claims = sum(r.n_predicted_claims for r in records)
    n_supported = sum(r.n_predicted_claims_supported for r in records)
    n_gold = sum(r.n_gold_claims for r in records)
    n_gold_covered = sum(r.n_gold_claims_covered for r in records)

    precision = (n_supported / n_claims) if n_claims > 0 else None
    recall = (n_gold_covered / n_gold) if n_gold > 0 else None

    return PrecisionRecall(
        precision=precision,
        recall=recall,
        n_claims=n_claims,
        n_supported=n_supported,
        n_gold_claims=n_gold,
        n_gold_covered=n_gold_covered,
    )


def unsupported_claim_rate(records: list[ClaimSupportRecord]) -> float | None:
    """Fraction of asserted claims that are NOT supported by cited evidence.

    Equivalent to (1 - precision) but kept as its own function because
    it's reported as its own row in the paper's metrics table and
    because callers should not assume it's always derived from
    precision (e.g. it may be computed on a different, larger sample
    than a precision figure that excludes abstentions differently).
    """
    n_claims = sum(r.n_predicted_claims for r in records)
    if n_claims == 0:
        return None
    n_unsupported = sum(
        r.n_predicted_claims - r.n_predicted_claims_supported for r in records
    )
    return n_unsupported / n_claims


# --------------------------------------------------------------------------
# Verification / Escalation: precision, recall, F1 on a binary flag
# --------------------------------------------------------------------------


@dataclass
class BinaryClassificationResult:
    precision: float | None
    recall: float | None
    f1: float | None
    tp: int
    fp: int
    fn: int
    tn: int


def escalation_precision_recall_f1(
    predicted_positive: list[bool], gold_positive: list[bool]
) -> BinaryClassificationResult:
    """Precision/recall/F1 for a binary "flag" decision.

    Reused for two rows of the metrics table with different inputs:
      - Verification: predicted = "verifier flagged unsupported/
        contradictory", gold = "case was a deliberately injected hard
        negative".
      - Escalation: predicted = "answer was escalated", gold = "SME
        says this needed review".

    Positive = the "flagged" / "needs review" class. Precision and
    recall are None when their denominator is 0 (no positives
    predicted / no positives in gold, respectively) rather than
    silently reporting 0.0, which would understate a perfect-but-rare
    detector.
    """
    if len(predicted_positive) != len(gold_positive):
        raise ValueError("predicted_positive and gold_positive must be the same length")

    tp = sum(1 for p, g in zip(predicted_positive, gold_positive) if p and g)
    fp = sum(1 for p, g in zip(predicted_positive, gold_positive) if p and not g)
    fn = sum(1 for p, g in zip(predicted_positive, gold_positive) if not p and g)
    tn = sum(1 for p, g in zip(predicted_positive, gold_positive) if not p and not g)

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return BinaryClassificationResult(precision=precision, recall=recall, f1=f1, tp=tp, fp=fp, fn=fn, tn=tn)


# --------------------------------------------------------------------------
# Calibration: Brier score, reliability bins / ECE
# --------------------------------------------------------------------------


def brier_score(confidences: list[float], outcomes: list[bool]) -> float:
    """Mean squared error between predicted confidence and binary outcome.

    `outcomes[i]` is whatever "the confidence was justified" means for
    the decision being scored (e.g. "auto-finalized answer was
    correct", or "escalation call matched the gold label") — the
    caller defines that, this function only does the arithmetic.

    Maps to "Calibration: Brier score" in
    specs/11-evaluation-and-baselines.md.
    """
    if len(confidences) != len(outcomes):
        raise ValueError("confidences and outcomes must be the same length")
    if not confidences:
        raise ValueError("need at least one record to compute a Brier score")
    return sum((c - float(o)) ** 2 for c, o in zip(confidences, outcomes)) / len(confidences)


@dataclass
class ReliabilityBin:
    bin_lower: float
    bin_upper: float
    n: int
    mean_confidence: float | None
    mean_outcome: float | None


@dataclass
class ReliabilityReport:
    bins: list[ReliabilityBin]
    ece: float


def reliability_bins(
    confidences: list[float], outcomes: list[bool], n_bins: int = 10
) -> ReliabilityReport:
    """Bin confidences for a reliability diagram and compute ECE.

    Expected Calibration Error = sum over bins of
    (bin count / total) * |mean_confidence - mean_outcome|.
    """
    if len(confidences) != len(outcomes):
        raise ValueError("confidences and outcomes must be the same length")
    if not confidences:
        raise ValueError("need at least one record to compute reliability bins")

    edges = [i / n_bins for i in range(n_bins + 1)]
    bins: list[ReliabilityBin] = []
    total = len(confidences)
    ece = 0.0

    for i in range(n_bins):
        lower, upper = edges[i], edges[i + 1]
        in_bin = [
            (c, o)
            for c, o in zip(confidences, outcomes)
            # last bin is closed on both ends so confidence == 1.0 lands somewhere
            if (lower <= c < upper) or (i == n_bins - 1 and c == upper)
        ]
        if in_bin:
            mean_conf = sum(c for c, _ in in_bin) / len(in_bin)
            mean_out = sum(float(o) for _, o in in_bin) / len(in_bin)
            ece += (len(in_bin) / total) * abs(mean_conf - mean_out)
        else:
            mean_conf = None
            mean_out = None
        bins.append(
            ReliabilityBin(bin_lower=lower, bin_upper=upper, n=len(in_bin), mean_confidence=mean_conf, mean_outcome=mean_out)
        )

    return ReliabilityReport(bins=bins, ece=ece)


# --------------------------------------------------------------------------
# Operations: latency, cost
# --------------------------------------------------------------------------


@dataclass
class CostLatencyRecord:
    question_id: str
    stage: str
    latency_ms: float
    cost_usd: float


@dataclass
class CostLatencySummary:
    n: int
    median_latency_ms: float
    p95_latency_ms: float
    total_cost_usd: float
    mean_cost_usd: float


def _percentile(data: list[float], pct: float) -> float:
    """pct in (0, 100). Falls back gracefully for tiny samples.

    Uses the "inclusive" quantile method (data treated as spanning its
    own min..max) rather than "exclusive", so a percentile never
    extrapolates past the actually-observed max — important for the
    small samples a quick dev-split check will have, where an
    "exclusive" P95 can otherwise land above every recorded value and
    look like a bug.
    """
    if len(data) == 1:
        return data[0]
    if not (0 < pct < 100):
        raise ValueError("pct must be between 0 and 100 exclusive")
    quantile_points = statistics.quantiles(data, n=100, method="inclusive")
    index = max(0, min(len(quantile_points) - 1, math.ceil(pct) - 1))
    return quantile_points[index]


def cost_latency_summary(records: list[CostLatencyRecord]) -> CostLatencySummary:
    """Median/P95 latency and total/mean cost across records.

    Maps to "Operations: median/P95 latency, tokens/API cost" in
    specs/11-evaluation-and-baselines.md. Call once per stage (filter
    `records` by `.stage` first) and once across all stages for the
    end-to-end figure — this function doesn't group for you, on
    purpose, so the caller controls exactly what's being summarized.
    """
    if not records:
        raise ValueError("need at least one record to summarize cost/latency")
    latencies = [r.latency_ms for r in records]
    costs = [r.cost_usd for r in records]
    return CostLatencySummary(
        n=len(records),
        median_latency_ms=statistics.median(latencies),
        p95_latency_ms=_percentile(latencies, 95),
        total_cost_usd=sum(costs),
        mean_cost_usd=sum(costs) / len(costs),
    )
