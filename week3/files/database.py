import os
import subprocess
from typing import Tuple

# ---------------------------------------------------------------------------
# Connection parameters — pulled from environment with sensible defaults
# ---------------------------------------------------------------------------
_host     = os.environ.get("PGHOST", "localhost")
_port     = os.environ.get("PGPORT", "5432")
_user     = os.environ.get("PGUSER", "utsavacharya")
_database = os.environ.get("PGDB", "postgres")
_password = os.environ.get("PGPASSWORD", os.environ.get("PASSWORD", "mysecretpassword"))


def run_select_as_csv(query: str) -> Tuple[bool, str, str]:
    """Run a SELECT query via psql and return the result as CSV text.

    Uses PostgreSQL's COPY … TO STDOUT so the output always includes a
    header row.  The caller receives a three-element tuple:

        (ok, csv_text, error_message)

    *ok* is True only when psql exits with code 0.  On failure *csv_text*
    will be an empty string and *error_message* will contain psql's stderr.
    """
    env = {**os.environ, "PGPASSWORD": _password}

    # Strip trailing semicolon before wrapping inside COPY(…)
    inner = query.strip().rstrip(";")
    copy_statement = f"COPY ({inner}) TO STDOUT WITH CSV HEADER;"

    cmd = [
        "psql",
        "-h", _host,
        "-p", _port,
        "-U", _user,
        "-d", _database,
        "-c", copy_statement,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )

    ok = result.returncode == 0
    return ok, result.stdout, result.stderr
