# 03 — Orchestrator

Status: living document. Owns: cross-cutting reliability/audit
requirements, not a "Must-have FR" of its own — it's what makes
FR1–FR10 measurable and NFR3/NFR5/NFR7/NFR8 true.

## Responsibility

Maintains per-question state, drives the stage sequence in
`specs/01-architecture.md`, retries failed stages, stamps every
record with config/version IDs, and emits the audit trail.

## Interface

```
Orchestrator.run(question: Question, config: ExperimentConfig) -> Answer
```

Internally this is a loop over stage functions, each with the shape:

```
stage_fn(state: PipelineState, config: ExperimentConfig) -> PipelineState
```

`PipelineState` bundles the current `Question`, `Answer`-in-progress,
retrieved `EvidenceChunk`s, and the latest `VerificationResult` — see
`src/trustilo/common/schemas.py`. Stages must be **pure functions of
their input state**: no hidden global mutation, no reading state that
wasn't explicitly passed in. This is what makes idempotent retries
possible.

## Idempotency and retries (NFR5)

- Every stage call is keyed by `(question_id, stage_name, attempt)`.
- Before executing a stage, check whether a persisted result already
  exists for that key; if so, return it instead of re-running (avoids
  double-charging LLM cost on retry and avoids corrupting a sibling
  question's state).
- A failed stage must leave the question in the *last successfully
  completed* state, never a half-written one. Wrap the "compute, then
  persist" pair in a transaction (or an outbox pattern if compute
  happens outside the DB transaction, e.g. an LLM call).
- Acceptance test for this spec: fault-injection tests that kill the
  process mid-stage must show the question resumable from stored
  state with no corruption of unrelated questions (NFR5's literal
  success criterion).

## Retry budget

- Stage-level transient failures (timeouts, rate limits): retry with
  backoff, bounded attempts, via `tenacity` or equivalent — this is
  infra retry, unrelated to the *verification* retry.
- The **verification → retrieval** retry described in
  `specs/01-architecture.md` is a single, explicit, orchestrator-
  managed transition, not a generic retry — cap it at one cycle per
  question and record that it happened in the `AuditEvent` trail.

## Config and version stamping (NFR7)

Every `Answer`, `VerificationResult`, and `EscalationDecision` records
which `ExperimentConfig.config_id` produced it (model IDs, retriever
config, verifier config, thresholds). This is what makes
`specs/11-evaluation-and-baselines.md` possible — without it you can't
attribute a metric change to a specific component swap.

## Audit events (NFR3)

Emit one `AuditEvent` per state transition (see
`specs/02-data-model.md`), including:
- stage entered/exited, with timing
- retrieval query issued and evidence chunk IDs returned
- verifier decision and reason
- escalation decision and reason codes
- reviewer action (in `specs/08-escalation-and-review.md`)

A finalized answer must be reconstructable purely from its
`AuditEvent` chain — 100% of finalized answers, per NFR3's success
criterion. Write a test that walks the chain for a sample of
finalized answers and asserts every referenced ID resolves.

## Cost/latency logging (NFR8)

Every LLM and retrieval call the orchestrator dispatches gets logged
with `stage`, `question_id`, `tenant_id`, `tokens_in/out` (or
retrieval call count), `latency_ms`, and `cost_usd`. This feeds the
`trustilo-eval-metrics` skill's operations metrics — don't compute
cost/latency ad hoc elsewhere.

## What NOT to put in the Orchestrator

- No drafting/verification/retrieval *logic* — it dispatches to those
  packages, it doesn't reimplement their behavior.
- No LLM calls directly — even orchestrator-level decisions that might
  want an LLM (there generally shouldn't be any in MVP) go through
  `common/llm_provider.py`.
