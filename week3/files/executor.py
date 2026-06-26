"""executor.py — thin wrapper around database.run_select_as_csv.

Adds a basic allow-list check so we never accidentally run mutating
statements, then writes successful output to disk as CSV.
"""

from __future__ import annotations

from typing import Tuple

from database import run_select_as_csv

# Keywords that must never appear in a generated query
_BLOCKED_KEYWORDS = (
    "DELETE ",
    "DROP ",
    "UPDATE ",
    "INSERT ",
    "ALTER ",
    "TRUNCATE ",
)


def run_query(sql: str, dest: str) -> Tuple[bool, bool, str]:
    """Execute *sql* and write CSV output to *dest*.

    Returns ``(success, retry_used, message)`` so callers can track
    whether a fallback path was taken.

    Parameters
    ----------
    sql:
        A SELECT statement to execute.
    dest:
        Filesystem path where the CSV result should be written.
    """
    normalised = sql.strip().upper()
    for kw in _BLOCKED_KEYWORDS:
        if kw in normalised:
            return False, False, f"Blocked keyword detected: {kw.strip()}"

    ok, csv_text, stderr = run_select_as_csv(sql)

    if ok:
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(csv_text)
        return True, False, "OK"

    # --- best-effort diagnosis -----------------------------------------------
    lines = stderr.strip().splitlines()
    last_line = lines[-1] if lines else "Unknown error"

    if "column" in stderr.lower() and "does not exist" in stderr.lower():
        last_line = "Column missing error; no automatic fix applied"

    return False, False, last_line
