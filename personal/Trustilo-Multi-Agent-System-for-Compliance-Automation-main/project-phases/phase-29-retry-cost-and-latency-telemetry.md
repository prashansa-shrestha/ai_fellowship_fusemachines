# Phase 29 — Retry, cost, and latency telemetry

**Feature branch:** `codex/feature-29-operations-telemetry`  
**Depends on:** Phases 03 and 27  
**Traceability:** `specs/03-orchestrator.md`, `specs/11-evaluation-and-baselines.md`; NFR4, NFR8

## Goal

Make bounded retries and per-question operational cost measurable across every provider and retrieval call.

## Implementation

- Add structured events containing stage, question, tenant, attempt, latency, token counts/retrieval count, estimated cost, model, and config ID.
- Centralize timeout/backoff policy with bounded attempts.
- Redact prompts, evidence text, credentials, and sensitive payloads from normal telemetry.
- Provide aggregation inputs for median/P95 latency and cost summaries.

## Unit tests

- Success, timeout, rate limit, retry exhaustion, and unknown-cost cases with a fake clock.
- One event per attempt plus a correct final summary.
- Secret/content redaction.
- Semantic requery remains distinguishable from infrastructure retries.

## Done when

Every measured call has complete operational metadata, safe logs, and enough information to evaluate NFR4/NFR8 without ad hoc calculations.
