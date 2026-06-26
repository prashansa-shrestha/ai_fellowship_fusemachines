"""main.py — evaluation pipeline entry-point.

Reads decompositions from task_2.md, generates and executes SQL for each,
compares results against ground-truth CSVs, and writes a summary report.
"""

from __future__ import annotations

import csv
import pathlib

from executor import run_query
from sql_generator import generate_sql, parse_decompositions
from validator import compare_csv

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

_ROOT          = pathlib.Path(__file__).parent
_GENERATED_DIR = _ROOT / "generated_outputs"
_GROUND_DIR    = _ROOT / "sql_outputs"

_GENERATED_DIR.mkdir(exist_ok=True)

# Report columns
_HEADERS = [
    "idx",
    "question",
    "sql",
    "executed",
    "correct_result",
    "retry_needed",
    "status",
]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def _ground_truth_path(idx: int) -> pathlib.Path | None:
    """Return the ground-truth CSV for query *idx*, or None if absent."""
    prefix  = f"{idx:02d}_"
    matches = list(_GROUND_DIR.glob(prefix + "*.csv"))
    return matches[0] if matches else None


def run_pipeline() -> None:
    decompositions = parse_decompositions(str(_ROOT / "task_2.md"))
    rows = []

    for idx, decomp in enumerate(decompositions, start=1):
        question = decomp["question"]
        dest     = str(_GENERATED_DIR / f"{idx:02d}.csv")

        # --- SQL generation --------------------------------------------------
        try:
            sql = generate_sql(decomp)
        except Exception as exc:  # noqa: BLE001
            rows.append((idx, question, "", False, False, True, f"gen_error: {exc}"))
            continue

        # --- Execution -------------------------------------------------------
        ok, retry_used, msg = run_query(sql, dest)

        if not ok:
            rows.append((idx, question, sql, False, False, retry_used, msg))
            continue

        # --- Validation against ground truth ---------------------------------
        gt_path = _ground_truth_path(idx)
        if gt_path is None:
            status  = "mismatch:missing_file"
            correct = False
        else:
            correct, reason = compare_csv(dest, str(gt_path))
            status = "match" if correct else f"mismatch:{reason}"

        rows.append((idx, question, sql, True, correct, retry_used, status))

    # --- Write report --------------------------------------------------------
    report_path = _ROOT / "evaluation_report.csv"
    with open(report_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(_HEADERS)
        writer.writerows(rows)

    print(f"Pipeline complete — report saved to {report_path}")


if __name__ == "__main__":
    run_pipeline()
