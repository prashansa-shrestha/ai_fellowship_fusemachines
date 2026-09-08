# Phase 24 — One-shot retrieval revision

**Feature branch:** `codex/feature-24-one-shot-requery`  
**Depends on:** Phases 17 and 23  
**Traceability:** `specs/01-architecture.md`, `specs/05-retrieval.md`, `specs/07-verification.md`; FR7, NFR5

## Goal

Allow the verifier to request one targeted query revision when weak support appears to be a retrieval miss.

## Implementation

- Emit `requested_requery` and a structured revised query only for eligible retrieval-miss signals.
- Keep original and revised queries distinct and auditable.
- Ensure the second verification result cannot request another retry.
- Leave loop enforcement to the orchestrator while also guarding it in the verification interface.

## Unit tests

- Eligible weak-support request, ineligible contradiction/staleness cases, and empty revised query.
- Second-pass request is forced off.
- Original question remains unchanged.
- Retry metadata serializes and persists correctly.

## Done when

Verification can describe one useful retrieval revision, but no code path can create an open-ended verifier/retriever loop.
