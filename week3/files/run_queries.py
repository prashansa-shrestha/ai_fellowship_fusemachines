#!/usr/bin/env python3
"""run_queries.py — extract SQL blocks from benchmark_sql_answers.md and run them.

Each SQL block in the markdown must be preceded by a non-header, non-list line
that serves as the question label.  Results are written as CSV files under the
``sql_outputs/`` directory.  A summary manifest is written at the end.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess

# ---------------------------------------------------------------------------
# Connection settings
# ---------------------------------------------------------------------------
_HOST     = "localhost"
_PORT     = "5432"
_USER     = "utsavacharya"
_PASSWORD = "mysecretpassword"
_DB       = "postgres"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_MARKDOWN_FILE = "benchmark_sql_answers.md"
_OUTPUT_DIR    = pathlib.Path("sql_outputs")
_OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BLOCK_PATTERN = re.compile(
    r"\n(?P<question>[^\n#\-\*][^\n]+?)\n\n```sql\n(?P<sql>.*?)\n```",
    re.DOTALL,
)


def _sanitise_filename(text: str, max_len: int = 100) -> str:
    clean = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_")
    return clean[:max_len]


def _run_copy(sql: str, env: dict) -> subprocess.CompletedProcess:
    inner       = sql.strip().rstrip(";")
    copy_cmd    = f"COPY ({inner}) TO STDOUT WITH CSV HEADER;"
    cmd         = ["psql", "-h", _HOST, "-p", _PORT, "-U", _USER, "-d", _DB, "-c", copy_cmd]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    with open(_MARKDOWN_FILE, encoding="utf-8") as fh:
        content = fh.read()

    matches = _BLOCK_PATTERN.findall(content)
    if not matches:
        raise SystemExit(f"No SQL blocks found in {_MARKDOWN_FILE!r}")

    env = {**os.environ, "PGPASSWORD": _PASSWORD}
    summary: list[tuple] = []

    for i, (question, sql) in enumerate(matches, start=1):
        filename = f"{i:02d}_{_sanitise_filename(question)}.csv"
        out_path = _OUTPUT_DIR / filename

        print(f"[{i:02d}] {question.strip()}")
        proc = _run_copy(sql, env)

        if proc.returncode != 0:
            err_path = out_path.with_suffix(".csv.err.txt")
            err_path.write_text(proc.stderr, encoding="utf-8")
            print(f"      ✗  error — see {err_path}")
            summary.append((question, out_path, False, err_path))
            continue

        out_path.write_text(proc.stdout, encoding="utf-8")
        line_count = len(proc.stdout.splitlines())
        print(f"      ✓  {line_count} lines → {out_path}")
        summary.append((question, out_path, True, None))

    # Write manifest
    manifest = _OUTPUT_DIR / "summary.txt"
    with open(manifest, "w", encoding="utf-8") as fh:
        for q, p, ok, err in summary:
            status = "OK" if ok else "ERROR"
            fh.write(f"{p}\t{status}\t{err or ''}\t{q}\n")

    print(f"\nDone — {len(matches)} queries processed.")
    print(f"Outputs : {_OUTPUT_DIR}/")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
