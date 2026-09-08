# Trustilo implementation phases

This directory turns the MVP specifications into 40 small, sequential delivery phases. Each phase is intended to be completed on its named feature branch, pushed to the existing remote, reviewed in a pull request, and merged into `main` before the next phase branches from the updated `main`.

## Branch workflow

1. Update local `main` from the existing upstream.
2. Create the branch named in the phase file.
3. Implement only that phase's scope and tests.
4. Run the listed verification commands.
5. Push the feature branch and open a pull request into `main`.
6. Merge only after the phase's acceptance criteria pass; then begin the next phase from the new `main`.

The branch names use the repository convention `codex/feature-<phase>-<slug>`. They are recommendations, not branches created by this planning change.

## Phase map

| Phase | Focus | Main requirements | Test level |
|---|---|---|---|
| 01 | Scope guard and development baseline | NFR7 | Unit/tooling |
| 02 | Canonical schemas and invariants | FR3, FR5, FR6, NFR9 | Unit |
| 03 | Configuration and LLM provider boundary | NFR7 | Unit |
| 04 | Persistence and repository contracts | NFR2, NFR3, NFR5 | Unit |
| 05 | Foundation integration checkpoint | NFR2, NFR3, NFR5, NFR7 | Integration |
| 06 | Evidence-document ingestion | FR3 | Unit |
| 07 | Chunking, versions, and supersession | FR3, NFR2 | Unit |
| 08 | Text and CSV questionnaire ingestion | FR1 | Unit |
| 09 | XLSX questionnaire ingestion | FR1, FR10 | Unit |
| 10 | Intake/knowledge integration checkpoint | FR1, FR3 | Integration |
| 11 | PDF ingestion and low-confidence flags | FR1 | Unit |
| 12 | Domain and answer-type classification | FR2 | Unit/eval |
| 13 | Duplicate and novelty detection | FR2, FR11 | Unit |
| 14 | Dense retrieval | FR4, NFR2 | Unit |
| 15 | Sparse retrieval | FR4, NFR2 | Unit |
| 16 | Hybrid fusion | FR4, H2 | Unit/eval |
| 17 | Re-ranking and evidence filters | FR4, NFR2 | Unit |
| 18 | Retrieval integration checkpoint | FR4, NFR2, H2 | Integration/eval |
| 19 | Deterministic grounded drafting | FR5, FR6, NFR1 | Unit |
| 20 | Provider-backed structured drafting | FR5, NFR7 | Unit/contract |
| 21 | Citation resolution and abstention gates | FR5, FR6, NFR1, NFR2 | Unit |
| 22 | Independent support verification | FR7 | Unit |
| 23 | Contradiction, freshness, and precedent checks | FR7, H3 | Unit |
| 24 | One-shot retrieval revision | FR7, NFR5 | Unit |
| 25 | Core RAG integration checkpoint | FR4–FR7, NFR1 | Integration |
| 26 | Orchestrator state machine | NFR3, NFR5 | Unit |
| 27 | Checkpointing and idempotent resume | NFR5 | Unit/fault injection |
| 28 | Immutable audit trail and reconstruction | NFR3 | Unit/integration |
| 29 | Retry, cost, and latency telemetry | NFR4, NFR8 | Unit |
| 30 | Orchestrator integration checkpoint | NFR3–NFR5, NFR8 | Integration |
| 31 | Escalation policy and reason codes | FR8, NFR9, H5 | Unit |
| 32 | Threshold calibration | FR8, H5 | Eval |
| 33 | Review-task API and decisions | FR9 | Unit/API |
| 34 | Reviewer console | FR9, NFR6 | UI unit |
| 35 | Human-review integration checkpoint | FR8, FR9, NFR6, NFR9 | Integration/E2E |
| 36 | Original-format export | FR10 | Unit/integration |
| 37 | Coverage and confidence reporting | FR10 | Unit |
| 38 | Approved-edit reuse | FR11 | Unit/integration |
| 39 | Baselines, ablations, and error taxonomy | H1–H5, NFR8 | Eval |
| 40 | Security, CI, and MVP acceptance | All MVP Must requirements | Full system |

## Integration checkpoint rule

Checkpoint phases do not add unrelated features. They join the preceding components, add cross-module fixtures and failure-path coverage, and must pass before later phases start. The final checkpoint runs the frozen held-out benchmark only after configuration and thresholds have been frozen on the development split.

## Scope boundary

These phases implement the MVP in `specs/00-overview-and-mvp-scope.md`. Framework Mapping (FR12), enterprise SSO/RBAC, portal integrations, multilingual support, production regional deployment, and autonomous fine-tuning remain excluded unless explicitly authorized as post-MVP work.
