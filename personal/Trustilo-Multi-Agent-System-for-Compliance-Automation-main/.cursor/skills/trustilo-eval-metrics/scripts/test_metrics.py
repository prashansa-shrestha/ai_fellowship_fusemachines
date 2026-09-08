"""Regression tests for metrics.py.

Standard-library `unittest`, deliberately — this skill promises to run
with no install step, so its own tests shouldn't need one either.

Run with:
    python -m unittest test_metrics.py -v
(from this directory, or `python -m unittest discover` from the repo
root once these are wired into the main test suite).
"""

from __future__ import annotations

import unittest

from metrics import (
    ClaimSupportRecord,
    CostLatencyRecord,
    brier_score,
    claim_support_precision_recall,
    cost_latency_summary,
    escalation_precision_recall_f1,
    mean_reciprocal_rank,
    mean_recall_at_k,
    reciprocal_rank,
    recall_at_k,
    reliability_bins,
    unsupported_claim_rate,
)


class TestRetrieval(unittest.TestCase):
    def test_recall_at_k_partial_hit(self):
        self.assertAlmostEqual(recall_at_k(["c1", "c2"], ["c3", "c1"], k=2), 0.5)

    def test_recall_at_k_beyond_k_does_not_count(self):
        # c2 is present but only at rank 3, outside k=2
        self.assertAlmostEqual(recall_at_k(["c1", "c2"], ["c1", "c3", "c2"], k=2), 0.5)

    def test_recall_at_k_empty_gold_is_none(self):
        self.assertIsNone(recall_at_k([], ["c1"], k=5))

    def test_mean_recall_at_k(self):
        gold = [["c1", "c2"], ["c9"]]
        retrieved = [["c1", "c2"], ["c1"]]
        self.assertAlmostEqual(mean_recall_at_k(gold, retrieved, k=10), 0.5)

    def test_reciprocal_rank_first_hit(self):
        self.assertAlmostEqual(reciprocal_rank(["c2"], ["c1", "c2", "c3"]), 0.5)

    def test_reciprocal_rank_no_hit_is_zero(self):
        self.assertEqual(reciprocal_rank(["c9"], ["c1", "c2"]), 0.0)

    def test_mrr(self):
        gold = [["c1"], ["c9"]]
        retrieved = [["c1"], ["c1", "c2"]]
        self.assertAlmostEqual(mean_reciprocal_rank(gold, retrieved), 0.5)


class TestGroundedness(unittest.TestCase):
    def test_precision_recall_basic(self):
        records = [
            ClaimSupportRecord("q1", n_predicted_claims=2, n_predicted_claims_supported=2, n_gold_claims=2, n_gold_claims_covered=2),
            ClaimSupportRecord("q2", n_predicted_claims=1, n_predicted_claims_supported=0, n_gold_claims=1, n_gold_claims_covered=0),
        ]
        pr = claim_support_precision_recall(records)
        self.assertAlmostEqual(pr.precision, 2 / 3)
        self.assertAlmostEqual(pr.recall, 2 / 3)
        self.assertIsNotNone(pr.f1)

    def test_abstained_answer_excluded_from_precision_denominator(self):
        # abstained answer: 0 predicted claims, should not count as a
        # 0/0 -> "perfect" or crash; overall precision should reflect
        # only the other record.
        records = [
            ClaimSupportRecord("q1", n_predicted_claims=0, n_predicted_claims_supported=0, n_gold_claims=1, n_gold_claims_covered=0),
            ClaimSupportRecord("q2", n_predicted_claims=2, n_predicted_claims_supported=1, n_gold_claims=2, n_gold_claims_covered=1),
        ]
        pr = claim_support_precision_recall(records)
        self.assertAlmostEqual(pr.precision, 0.5)  # 1/2, the abstained record contributes 0 claims

    def test_unsupported_claim_rate(self):
        records = [
            ClaimSupportRecord("q1", n_predicted_claims=4, n_predicted_claims_supported=3, n_gold_claims=4, n_gold_claims_covered=3),
        ]
        self.assertAlmostEqual(unsupported_claim_rate(records), 0.25)

    def test_unsupported_claim_rate_no_claims_is_none(self):
        records = [ClaimSupportRecord("q1", 0, 0, 0, 0)]
        self.assertIsNone(unsupported_claim_rate(records))


class TestBinaryClassification(unittest.TestCase):
    def test_perfect_detector(self):
        result = escalation_precision_recall_f1([True, False, True], [True, False, True])
        self.assertEqual(result.precision, 1.0)
        self.assertEqual(result.recall, 1.0)
        self.assertEqual(result.f1, 1.0)

    def test_over_flagging_hurts_precision_not_recall(self):
        # predicts positive every time; gold has 1 true positive out of 3
        result = escalation_precision_recall_f1([True, True, True], [True, False, False])
        self.assertAlmostEqual(result.precision, 1 / 3)
        self.assertEqual(result.recall, 1.0)

    def test_no_predicted_positives_is_none_precision(self):
        result = escalation_precision_recall_f1([False, False], [True, False])
        self.assertIsNone(result.precision)
        self.assertEqual(result.recall, 0.0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            escalation_precision_recall_f1([True], [True, False])


class TestCalibration(unittest.TestCase):
    def test_brier_score_perfect_calibration_is_zero(self):
        self.assertAlmostEqual(brier_score([1.0, 0.0], [True, False]), 0.0)

    def test_brier_score_worst_case_is_one(self):
        self.assertAlmostEqual(brier_score([1.0, 0.0], [False, True]), 1.0)

    def test_reliability_bins_ece_zero_when_perfectly_calibrated(self):
        # every bucket's mean confidence matches its mean outcome
        confidences = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.1]
        outcomes = [True] * 9 + [False]
        report = reliability_bins(confidences, outcomes, n_bins=10)
        self.assertGreaterEqual(report.ece, 0.0)
        self.assertLessEqual(report.ece, 1.0)


class TestOperations(unittest.TestCase):
    def test_p95_never_exceeds_observed_max(self):
        records = [
            CostLatencyRecord("q1", "drafting", 900, 0.01),
            CostLatencyRecord("q2", "drafting", 1200, 0.01),
            CostLatencyRecord("q3", "drafting", 1300, 0.01),
            CostLatencyRecord("q4", "drafting", 1400, 0.01),
        ]
        summary = cost_latency_summary(records)
        self.assertLessEqual(summary.p95_latency_ms, max(r.latency_ms for r in records))
        self.assertGreaterEqual(summary.p95_latency_ms, summary.median_latency_ms)

    def test_total_and_mean_cost(self):
        records = [
            CostLatencyRecord("q1", "drafting", 100, 0.01),
            CostLatencyRecord("q2", "drafting", 200, 0.03),
        ]
        summary = cost_latency_summary(records)
        self.assertAlmostEqual(summary.total_cost_usd, 0.04)
        self.assertAlmostEqual(summary.mean_cost_usd, 0.02)


if __name__ == "__main__":
    unittest.main()
