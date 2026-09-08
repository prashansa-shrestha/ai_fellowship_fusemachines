# Phase 03 — Configuration and LLM provider boundary

**Feature branch:** `codex/feature-03-provider-config`  
**Depends on:** Phase 02  
**Traceability:** `specs/01-architecture.md`, `specs/03-orchestrator.md`, `specs/13-tech-stack-and-repo-layout.md`; NFR7

## Goal

Ensure pipeline stages depend on a vendor-neutral LLM contract and frozen, versioned configuration.

## Implementation

- Define provider request/response types, structured-output support, usage metadata, timeout behavior, and deterministic test doubles.
- Load settings from environment-backed configuration without exposing secret values in logs.
- Validate `ExperimentConfig` model IDs, retriever mode, verifier settings, thresholds, and unique `config_id`.
- Prohibit direct vendor SDK imports from stage packages through a lightweight architecture check.

## Unit tests

- Fake-provider success, malformed structured output, timeout, and rate-limit cases.
- Configuration validation and secret-redaction tests.
- Test that stage modules import only the common provider abstraction.

## Done when

Any supported model provider can be swapped behind one interface, and every generated artifact can identify the exact experiment configuration that produced it.
