# Phase 40 — Security, CI, and MVP acceptance

**Feature branch:** `codex/feature-40-mvp-acceptance`  
**Depends on:** Phases 01–39  
**Traceability:** all MVP specs and all Must requirements in `specs/14-requirements-traceability.md`

## Goal

Complete cross-cutting security/governance checks, automate regression gates, run the frozen held-out benchmark once, and document the honest MVP acceptance result.

## Implementation

- Document encryption in transit/at rest, least-privilege roles, secrets management, retention/deletion, and prototype deployment boundaries.
- Add CI gates for unit tests, integration tests, tenant-isolation adversarial tests, schema/spec drift, and secret scanning.
- Freeze code/config/thresholds, then run B0/B1/B2/P and required ablations on the held-out test split.
- Conduct the pilot reviewer session and record human-factor metrics.
- Update requirement traceability only where the literal criterion has passed; leave gaps visible.

## Full-system tests

- Two-tenant questionnaire/evidence ingestion through export, audit reconstruction, review, and approved-edit reuse.
- Hard negatives for missing, misleading, contradictory, stale, and prompt-injection evidence.
- Fault injection, 100-question latency/cost run, and all FR/NFR acceptance metrics.
- Verify post-MVP features, especially FR12 and enterprise SSO/RBAC, are absent.

## Done when

Every Must requirement is either `verified` with named evidence or explicitly reported as unmet, benchmark integrity is preserved, and the repository is ready for an evidence-backed MVP pull request to `main`.
