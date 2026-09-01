#!/usr/bin/env python3
"""CLI entry point for the trustilo-eval-metrics skill.

Reads a JSONL file of per-question eval records and prints (and
optionally writes) the metrics table defined in
specs/11-evaluation-and-baselines.md. Each metric group is computed
only if the input records contain the fields it needs, so this works
whether you're checking retrieval alone or a full end-to-end baseline
run.

Expected record shape (all keys optional except question_id — include
whichever fields your current run actually has):

{
  "question_id": "q_0001",
  "gold_evidence_chunk_ids": ["c1", "c2"],
  "retrieved_chunk_ids": ["c3", "c1", "c5", "c2"],
  "n_predicted_claims": 3,
  "n_predicted_claims_supported": 3,
  "n_gold_claims": 3,
  "n_gold_claims_covered": 2,
  "escalated": false,
  "gold_needs_review": false,
  "verifier_flagged": false,
  "is_injected_hard_negative": false,
  "confidence": 0.82,
  "outcome_correct": true,
  "stage_latencies_ms": {"retrieval": 300, "drafting": 2500, "verification": 1400},
  "stage_costs_usd": {"retrieval": 0.001, "drafting": 0.008, "verification": 0.005}
}

Usage:
    python run_eval.py --input records.jsonl [--baseline P] [--k 10] [--out report.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from metrics import (
    ClaimSupportRecord,
    CostLatencyRecord,
    brier_score,
    claim_support_precision_recall,
    cost_latency_summary,
    escalation_precision_recall_f1,
    mean_reciprocal_rank,
    mean_recall_at_k,
    reliability_bins,
    unsupported_claim_rate,
)


def load_records(path: Path) -> list[dict]:
    records = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON — {e}") from e
    if not records:
        raise ValueError(f"{path}: no records found")
    return records


def build_report(records: list[dict], k: int) -> dict:
    report: dict = {"n_records": len(records)}

    # Retrieval
    if all("gold_evidence_chunk_ids" in r and "retrieved_chunk_ids" in r for r in records):
        gold = [r["gold_evidence_chunk_ids"] for r in records]
        retrieved = [r["retrieved_chunk_ids"] for r in records]
        report["retrieval"] = {
            f"recall_at_{k}": mean_recall_at_k(gold, retrieved, k),
            "mrr": mean_reciprocal_rank(gold, retrieved),
        }

    # Groundedness
    claim_fields = (
        "n_predicted_claims",
        "n_predicted_claims_supported",
        "n_gold_claims",
        "n_gold_claims_covered",
    )
    if all(all(f in r for f in claim_fields) for r in records):
        claim_records = [
            ClaimSupportRecord(
                question_id=r["question_id"],
                n_predicted_claims=r["n_predicted_claims"],
                n_predicted_claims_supported=r["n_predicted_claims_supported"],
                n_gold_claims=r["n_gold_claims"],
                n_gold_claims_covered=r["n_gold_claims_covered"],
            )
            for r in records
        ]
        pr = claim_support_precision_recall(claim_records)
        report["groundedness"] = {
            "claim_support_precision": pr.precision,
            "claim_support_recall": pr.recall,
            "claim_support_f1": pr.f1,
            "unsupported_claim_rate": unsupported_claim_rate(claim_records),
        }

    # Verification (on injected hard negatives)
    if all("verifier_flagged" in r and "is_injected_hard_negative" in r for r in records):
        result = escalation_precision_recall_f1(
            [r["verifier_flagged"] for r in records],
            [r["is_injected_hard_negative"] for r in records],
        )
        report["verification"] = asdict(result)

    # Escalation
    if all("escalated" in r and "gold_needs_review" in r for r in records):
        result = escalation_precision_recall_f1(
            [r["escalated"] for r in records],
            [r["gold_needs_review"] for r in records],
        )
        report["escalation"] = asdict(result)

    # Calibration
    if all("confidence" in r and "outcome_correct" in r for r in records):
        confidences = [r["confidence"] for r in records]
        outcomes = [r["outcome_correct"] for r in records]
        rel = reliability_bins(confidences, outcomes)
        report["calibration"] = {
            "brier_score": brier_score(confidences, outcomes),
            "ece": rel.ece,
        }

    # Operations — one summary per stage found in stage_latencies_ms/stage_costs_usd
    if all("stage_latencies_ms" in r and "stage_costs_usd" in r for r in records):
        stages = sorted({s for r in records for s in r["stage_latencies_ms"]})
        ops: dict = {}
        for stage in stages:
            stage_records = [
                CostLatencyRecord(
                    question_id=r["question_id"],
                    stage=stage,
                    latency_ms=r["stage_latencies_ms"][stage],
                    cost_usd=r["stage_costs_usd"][stage],
                )
                for r in records
                if stage in r["stage_latencies_ms"]
            ]
            ops[stage] = asdict(cost_latency_summary(stage_records))
        # end-to-end across all stages combined
        all_records = [
            CostLatencyRecord(
                question_id=r["question_id"],
                stage="__all__",
                latency_ms=sum(r["stage_latencies_ms"].values()),
                cost_usd=sum(r["stage_costs_usd"].values()),
            )
            for r in records
        ]
        ops["__end_to_end__"] = asdict(cost_latency_summary(all_records))
        report["operations"] = ops

    return report


def print_report(report: dict, baseline: str | None) -> None:
    header = f"Trustilo evaluation report" + (f" — baseline {baseline}" if baseline else "")
    print(header)
    print("=" * len(header))
    print(f"records: {report['n_records']}")
    for section, values in report.items():
        if section == "n_records":
            continue
        print(f"\n[{section}]")
        _print_section(values, indent=2)


def _print_section(values, indent: int) -> None:
    pad = " " * indent
    if isinstance(values, dict):
        for k, v in values.items():
            if isinstance(v, dict):
                print(f"{pad}{k}:")
                _print_section(v, indent + 2)
            else:
                formatted = f"{v:.4f}" if isinstance(v, float) else str(v)
                print(f"{pad}{k}: {formatted}")
    else:
        print(f"{pad}{values}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path, help="JSONL file of eval records")
    parser.add_argument("--baseline", default=None, help="Label only (e.g. B0/B1/B2/P) — not used to change scoring logic")
    parser.add_argument("--k", type=int, default=10, help="k for Recall@k (default 10)")
    parser.add_argument("--out", type=Path, default=None, help="Optional path to write the report as JSON")
    args = parser.parse_args()

    records = load_records(args.input)
    report = build_report(records, k=args.k)
    if args.baseline:
        report["baseline"] = args.baseline

    print_report(report, args.baseline)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2))
        print(f"\nwrote {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
