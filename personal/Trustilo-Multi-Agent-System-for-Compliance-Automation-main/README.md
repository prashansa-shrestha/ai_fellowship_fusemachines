# Trustilo

Trustilo is an evidence-grounded pipeline for answering security questionnaires. Its core rule is simple: a
material claim must point to approved tenant-scoped evidence; when evidence is missing, the safe answer is an
abstention.

## What works in this partial demo

The current local checkpoints can:

- parse UTF-8 text, CSV, and XLSX questionnaires and classify questions with transparent rules;
- retrieve active evidence from an in-memory, tenant-isolated lexical index;
- draft conservative claims directly from retrieved chunks with exact citations; and
- independently flag unsupported, mismatched, contradictory, stale, or future-dated citations.

These are deterministic demonstration components, not the finished production system. PostgreSQL hybrid retrieval,
LLM-backed drafting, orchestration, audit persistence, escalation, and the reviewer console are still to come.

## Quickstart

```bash
python3 -m pip install -e ".[dev]"
pytest -q tests/unit
```

The install command prepares Trustilo and its development tools in the active Python environment. The test command
runs the local schema and checkpoint behavior tests.

For a plain-language walkthrough, read [explain.md](explain.md). For an honest done/remaining ledger, read
[record.md](record.md). The engineering contracts and acceptance targets live in [specs/](specs/), starting with
[the MVP scope](specs/00-overview-and-mvp-scope.md).
