# 14 — Requirements Traceability

Status: **update this file whenever you start or finish work on a
requirement.** It's the single source of truth for "is FR7 actually
done," which matters both for your own planning and for grading
against the AIF submission's stated success criteria. The
`/trace-requirement` command and the `spec-compliance-auditor`
subagent both read and update this file — keep it accurate rather than
aspirational.

Status values: `not started` / `in progress` / `implemented` /
`verified` (verified = the success-criterion test actually passes on
real data, not just "code exists").

## Functional Requirements

| ID | Requirement | Priority | Success criterion | Spec | Module | Status |
|---|---|---|---|---|---|---|
| FR1 | Questionnaire ingestion | Must | ≥95% extraction correctness on curated format tests | `specs/04-intake-classification.md` | `src/trustilo/intake` | in progress |
| FR2 | Question classification | Must | ≥85% macro-F1 domain labels (or agreed simpler metric) | `specs/04-intake-classification.md` | `src/trustilo/intake` | in progress |
| FR3 | Knowledge ingestion | Must | Every indexed chunk has doc ID, version, source, tenant namespace | `specs/02-data-model.md`, `specs/12-security-and-governance.md` | `src/trustilo/knowledge_library` | not started |
| FR4 | Hybrid retrieval | Must | Evidence Recall@10 ≥90% on gold retrieval set | `specs/05-retrieval.md` | `src/trustilo/retrieval` | not started |
| FR5 | Grounded drafting | Must | ≥95% claim-support precision for auto-finalized answers | `specs/06-drafting.md` | `src/trustilo/drafting` | not started |
| FR6 | Citation generation | Must | 100% of auto-finalized answers have valid, traceable citations | `specs/06-drafting.md` | `src/trustilo/drafting` | not started |
| FR7 | Verification | Must | Detect ≥90% of injected unsupported/contradictory test answers | `specs/07-verification.md` | `src/trustilo/verification` | not started |
| FR8 | Confidence and escalation | Must | Needs-review recall ≥90%; precision ≥60% during pilot | `specs/08-escalation-and-review.md` | `src/trustilo/escalation` | not started |
| FR9 | Human review | Must | All reviewer decisions persisted and reflected in export | `specs/08-escalation-and-review.md`, `specs/09-reviewer-console.md` | `apps/reviewer-console`, `src/trustilo/escalation` | not started |
| FR10 | Export and report | Must | No answer/question misalignment in round-trip XLSX tests | `specs/10-export-audit-feedback.md` | `src/trustilo/export_audit` | not started |
| FR11 | Feedback capture | Should | Approved edit retrievable by a semantically similar later question | `specs/10-export-audit-feedback.md` | `src/trustilo/export_audit`, `src/trustilo/knowledge_library` | not started |
| FR12 | Framework mapping | Could / Post-MVP | Mapping precision measured separately; human confirmation required initially | `specs/00-overview-and-mvp-scope.md` (deferred) | — | not started (post-MVP, do not build without explicit ask) |

## Non-Functional Requirements

| ID | Requirement | Priority | Success criterion | Spec | Status |
|---|---|---|---|---|---|
| NFR1 | Groundedness | Must | ≥95% claim-support precision on held-out SME review; ≤2% unsupported-claim rate (stretch) | `specs/06-drafting.md`, `specs/07-verification.md` | not started |
| NFR2 | Security isolation | Must | Encryption in transit/at rest in deployment design; zero cross-tenant retrieval in tests | `specs/05-retrieval.md`, `specs/12-security-and-governance.md` | not started |
| NFR3 | Auditability | Must | 100% of finalized answers have reconstructable question/evidence/draft/verifier/reviewer/version lineage | `specs/03-orchestrator.md`, `specs/10-export-audit-feedback.md` | not started |
| NFR4 | Latency | Should | 100-question run < 15 minutes excluding human review, normal API availability | `specs/03-orchestrator.md` | not started |
| NFR5 | Reliability | Must | Idempotent retries; failed stage resumable from stored state in fault-injection tests | `specs/03-orchestrator.md` | not started |
| NFR6 | Usability | Should | Reviewer approves/edits without raw logs in ≥90% of flagged cases | `specs/09-reviewer-console.md` | not started |
| NFR7 | Maintainability | Should | Config/version IDs recorded per experiment; no hard dependency on one LLM vendor | `specs/03-orchestrator.md`, `specs/13-tech-stack-and-repo-layout.md` | not started |
| NFR8 | Cost observability | Should | Cost and latency logged per question and per agent for 100% of benchmark runs | `specs/03-orchestrator.md`, `specs/11-evaluation-and-baselines.md` | not started |
| NFR9 | Explainability | Must | Every escalated task has a machine-readable reason code and a human-readable explanation | `specs/08-escalation-and-review.md` | not started |

## Hypotheses

| ID | Hypothesis | Depends on | Status |
|---|---|---|---|
| H1 | Trustilo > B0/B1 on SME-rated evidence faithfulness | FR5–FR7, `specs/11-evaluation-and-baselines.md` | not tested |
| H2 | Hybrid retrieval > dense-only / sparse-only on Recall@10 | FR4 ablation | not tested |
| H3 | Verification + escalation reduces unsupported-claim rate vs. B1 | FR7, FR8 | not tested |
| H4 | Full pipeline reduces median human-review time vs. manual, at acceptable groundedness | FR9, human-factors metrics | not tested |
| H5 | Composite retrieval+verifier confidence beats generator-only confidence for escalation | FR8, NFR9 | not tested |

## How to update this file

When you finish work that satisfies a success criterion **on real
data** (not just "the code path exists"), change that row's status to
`verified` and note the evidence (a test name, a benchmark run ID) in
your PR description — this file itself stays terse. Use
`/trace-requirement FR7` (or any ID) to have the agent check current
status and propose the update.
