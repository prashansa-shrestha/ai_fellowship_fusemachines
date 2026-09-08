# Phase 26 — Orchestrator state machine

**Feature branch:** `codex/feature-26-orchestrator-state-machine`  
**Depends on:** Phase 25  
**Traceability:** `specs/01-architecture.md`, `specs/03-orchestrator.md`; NFR3, NFR5

## Goal

Implement the only component allowed to transition answers through the specified per-question state graph.

## Implementation

- Encode allowed statuses and transitions explicitly.
- Dispatch pure stage functions using `PipelineState` and `ExperimentConfig`.
- Reject skips, backward transitions, and post-finalization mutation.
- Manage the single verification-to-retrieval retry counter separately from infrastructure retries.
- Emit a transition event request for every state change.

## Unit tests

- Happy auto-finalization and escalation paths using fake stages.
- Every invalid transition and terminal-state mutation.
- Exactly one retrieval-revision cycle.
- One question's failure cannot mutate a sibling's state.

## Done when

The orchestrator owns sequencing without duplicating stage logic or making direct LLM calls, and every permitted path matches the architecture spec.
