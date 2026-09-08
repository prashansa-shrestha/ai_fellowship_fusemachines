# AGENTS.md — orchestrator

Owns: cross-cutting reliability/audit (NFR3, NFR5, NFR7, NFR8). Full
spec: `../../../specs/03-orchestrator.md`.

- Stage functions dispatched from here must be pure functions of
  `PipelineState` + `ExperimentConfig` (see `common/schemas.py`) — no
  hidden module-level state.
- Every stage call is keyed by `(question_id, stage_name, attempt)`
  for idempotent retries; check for an existing persisted result
  before recomputing.
- The verification→retrieval retry is capped at exactly one cycle —
  enforce the cap here even if Verification's own logic also tries to
  respect it (belt and suspenders).
- Emit an `AuditEvent` on every state transition. Don't let a stage
  write its result without also writing the corresponding event in
  the same logical operation.
- This package dispatches to other stages; it does not contain
  drafting/retrieval/verification logic itself, and it never calls an
  LLM provider SDK directly — see `common/llm_provider.py`.
