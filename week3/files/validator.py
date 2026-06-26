"""validator.py — CSV comparison helpers.

Row order is ignored; numeric values are compared with a small relative
tolerance so that floating-point representation differences don't cause
false failures.
"""

from __future__ import annotations

import csv
import math
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load(path: str) -> Tuple[List[str], List[tuple]]:
    """Return (header, rows) for the CSV at *path*."""
    with open(path, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        all_rows = list(reader)

    if not all_rows:
        return [], []

    header = all_rows[0]
    data   = [tuple(r) for r in all_rows[1:]]
    return header, data


def _cells_match(a: str, b: str, tolerance: float = 1e-6) -> bool:
    """Return True when two cell values are considered equal.

    Tries an exact string comparison first, then falls back to
    numeric comparison when both values parse as floats.
    """
    if a == b:
        return True
    try:
        return math.isclose(float(a), float(b), rel_tol=tolerance, abs_tol=tolerance)
    except (ValueError, TypeError):
        return False


def _rows_match(row_a: tuple, row_b: tuple) -> bool:
    if len(row_a) != len(row_b):
        return False
    return all(_cells_match(x, y) for x, y in zip(row_a, row_b))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_csv(generated: str, reference: str) -> Tuple[bool, str]:
    """Compare two CSV files, ignoring row order.

    Parameters
    ----------
    generated:
        Path to the file produced by the pipeline.
    reference:
        Path to the ground-truth file.

    Returns
    -------
    (ok, reason)
        *ok* is True when the files are considered equivalent.
    """
    try:
        gen_header, gen_rows = _load(generated)
        ref_header, ref_rows = _load(reference)
    except FileNotFoundError:
        return False, "missing_file"

    if gen_header != ref_header:
        return False, "header_mismatch"

    remaining = list(ref_rows)
    for gen_row in gen_rows:
        for idx, ref_row in enumerate(remaining):
            if _rows_match(gen_row, ref_row):
                remaining.pop(idx)
                break
        else:
            return False, "row_mismatch"

    if remaining:
        return False, "extra_rows"

    return True, "match"
