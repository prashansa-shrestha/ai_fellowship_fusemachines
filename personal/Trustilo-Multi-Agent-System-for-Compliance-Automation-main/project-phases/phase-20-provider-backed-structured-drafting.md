# Phase 20 — Provider-backed structured drafting

**Feature branch:** `codex/feature-20-structured-llm-drafting`  
**Depends on:** Phases 03 and 19  
**Traceability:** `specs/06-drafting.md`; FR5, FR6, NFR7

## Goal

Add configurable LLM drafting that returns canonical structured answers while retaining conservative abstention behavior.

## Implementation

- Build separated instruction and evidence-context messages through the common provider abstraction.
- Require JSON-schema output matching `Answer` and `Claim`.
- Validate cited chunk IDs against only the supplied, tenant-consistent evidence.
- On malformed or unsafe output, retry only within the infrastructure budget and then fail safely or abstain.
- Record model version and token/latency metadata.

## Tests

- Contract tests with fake provider responses for valid answer, abstention, malformed JSON, invented citations, and extra claims.
- Prompt-boundary test with instruction-like evidence.
- Provider swap test with identical canonical output.

## Done when

No provider response bypasses schema and citation validation, and stages remain free of direct vendor SDK dependencies.
