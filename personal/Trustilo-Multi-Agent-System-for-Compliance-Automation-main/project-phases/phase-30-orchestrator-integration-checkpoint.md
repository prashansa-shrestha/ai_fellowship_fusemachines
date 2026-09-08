# Phase 30 — Orchestrator integration checkpoint

**Feature branch:** `codex/feature-30-orchestrator-integration`  
**Depends on:** Phases 26–29  
**Traceability:** `specs/01-architecture.md`, `specs/03-orchestrator.md`; NFR3, NFR4, NFR5, NFR8

## Goal

Run the core pipeline under persisted orchestration and verify recovery, auditability, and telemetry across realistic outcomes.

## Integration tests

- Auto-finalize-ready, abstained, verifier-requery, and escalation-ready questions execute concurrently without state crossover.
- Kill/restart at each stage boundary and confirm safe resume with no duplicate provider call.
- Reconstruct every completed answer from audit events and resolve all references.
- Confirm one semantic requery maximum and bounded infrastructure retries.
- Produce per-question/stage latency, token, and cost summaries for a 100-question synthetic smoke run; compare with the 15-minute target without claiming held-out verification.

## Done when

The persisted pipeline is reliable and observable end to end, and any performance gap is recorded before escalation/UI work begins.
