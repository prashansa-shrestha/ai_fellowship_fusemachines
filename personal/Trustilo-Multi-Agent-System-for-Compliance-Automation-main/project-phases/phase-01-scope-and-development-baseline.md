# Phase 01 — Scope guard and development baseline

**Feature branch:** `codex/feature-01-scope-dev-baseline`  
**Depends on:** none  
**Traceability:** `specs/00-overview-and-mvp-scope.md`, `specs/13-tech-stack-and-repo-layout.md`; NFR7

## Goal

Establish a reproducible local development baseline without replacing the deterministic demo components already present.

## Implementation

- Confirm Python 3.11+ packaging, development dependencies, source layout, and test discovery.
- Document local setup, required environment variable names, PostgreSQL/pgvector expectations, and the MVP exclusions.
- Add or refine safe example configuration only; never commit credentials.
- Record the initial unit-test baseline and known gaps so later phases can distinguish regressions from unfinished work.

## Tests

- Add a smoke test that imports every current `trustilo` package.
- Verify configuration startup fails clearly when a required setting is absent.
- Run `pytest -q tests/unit` and record the result in the pull request.

## Done when

A new contributor can install the project, run unit tests, understand which services are optional for unit testing, and see that all post-MVP items are explicitly excluded.
