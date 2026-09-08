# Phase 27 — Checkpointing and idempotent resume

**Feature branch:** `codex/feature-27-idempotent-checkpoints`  
**Depends on:** Phase 26  
**Traceability:** `specs/03-orchestrator.md`; NFR5

## Goal

Persist stage outputs atomically so interrupted questions resume from their last successful state without duplicate work.

## Implementation

- Key each attempt by `(question_id, stage_name, attempt)` and reuse an existing completed result.
- Separate expensive computation from atomic persistence using a transaction/outbox-compatible boundary.
- Persist checkpoints after complete stage validation only.
- Track bounded infrastructure retries independently from the single semantic requery.

## Unit and fault-injection tests

- Crash before compute, after compute/before persist, and after persist.
- Resume returns the stored result without a second fake-provider charge.
- Concurrent duplicate attempt resolves deterministically.
- Interrupted question leaves unrelated questions unchanged.

## Done when

Fault injection demonstrates resumability and no duplicate side effects, meeting NFR5's literal acceptance behavior.
