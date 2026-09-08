# AGENTS.md — retrieval

Owns: **FR4** (hybrid retrieval), and this is where **NFR2** (tenant
isolation) is actually enforced. Full spec:
`../../../specs/05-retrieval.md`. Read
`../../../.cursor/rules/tenant-isolation-security.mdc` before writing
any query in this package.

- Every query filters by `tenant_id` in the query itself — never fetch
  broadly and filter in Python afterward. No exceptions, no "just for
  this internal admin tool" carve-outs.
- New query path → new adversarial isolation test (seed two tenants,
  query as one, assert zero cross-tenant rows). This is not optional
  polish; it's the acceptance test for this package.
- Accept an optional `revised_query` parameter for the one-shot
  verification retry (`specs/07-verification.md`) — log both the
  original and revised query on the audit trail.
- Ablation configurations (dense-only/sparse-only/hybrid,
  with/without rerank) are driven by `ExperimentConfig.retriever_config`,
  not by code branches — see `specs/11-evaluation-and-baselines.md`.
- If the `groundedness-reviewer` or `tenant-isolation-auditor` subagent
  flags something here, treat it as a blocking finding, not a
  suggestion — this package guards NFR2's zero-tolerance target.
