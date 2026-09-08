# AGENTS.md — common

Shared foundation every other package builds on. Full spec:
`../../../specs/02-data-model.md`.

- `schemas.py` is the canonical data model — every cross-stage payload
  uses these Pydantic models, not ad hoc dicts. The validators here
  (uncited-claim rejection, escalation reason codes, evidence
  provenance) encode load-bearing invariants, not style preferences —
  don't relax one to make a call site more convenient.
- `llm_provider.py` is the *only* place a vendor SDK (`anthropic`,
  `openai`, ...) should be imported. If you're about to `import
  anthropic` inside `drafting/` or `verification/`, stop — register a
  provider here instead and call `get_provider()`.
- `config.py` is the only place environment variables are read
  directly. Other modules take configuration as function arguments
  (often via `ExperimentConfig`), not by reaching into `os.environ`
  themselves — that's what keeps stage functions pure and testable.
- Changing a schema here means updating `specs/02-data-model.md` in
  the same commit, and probably running
  `.cursor/agents/spec-compliance-auditor.md` before calling it done.
