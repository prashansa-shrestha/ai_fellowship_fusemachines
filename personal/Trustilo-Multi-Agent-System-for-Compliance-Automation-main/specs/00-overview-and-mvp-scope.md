# 00 — Overview & MVP Scope

Status: living document. Source: `report/main.tex` §I–II.

## Problem

> How can security questionnaires be answered substantially faster
> while ensuring that every material claim is supported by current,
> customer-approved evidence and that uncertain answers are reliably
> routed to a human reviewer?

Manual response is accurate but slow. A direct LLM is fast but can
fabricate or use stale claims. Trustilo treats questionnaire response
as a sequence of separately-testable tasks (classify → retrieve →
draft → verify → escalate) rather than one generation call, so each
failure mode can be measured and fixed independently.

## Research question

Can a multi-agent, retrieval-grounded, verification-and-escalation
pipeline answer security questionnaires with higher evidence
faithfulness and lower human-review effort than a direct LLM or a
single-agent RAG baseline? (See `specs/11-evaluation-and-baselines.md`
for how this is tested — baselines B0/B1/B2 vs. proposed system P.)

## Hypotheses (all must be evaluated, not assumed)

| ID | Hypothesis |
|---|---|
| H1 | Trustilo achieves higher SME-rated evidence faithfulness than direct-LLM and single-agent RAG baselines. |
| H2 | Hybrid retrieval improves gold-evidence Recall@10 over dense-only or sparse-only retrieval. |
| H3 | Independent verification + escalation reduces the unsupported-claim rate vs. single-agent RAG. |
| H4 | The full pipeline reduces median human-review time per question vs. fully manual completion, at acceptable groundedness. |
| H5 | Confidence/escalation performs better combining retrieval+verifier features than thresholding generator self-confidence alone. |

## MVP — in scope

- Security/infrastructure questions in PDF, XLSX/CSV, or plain text.
- Manual upload of customer-approved policies, architecture/security
  docs, prior approved answers, SOC-style evidence extracts,
  penetration-test summaries.
- Orchestrator, Intake/Classification, Retrieval, Drafting,
  Verification, Escalation, and a lightweight Reviewer Console.
- Evidence-linked answer output, confidence/risk status, full
  processing trace.
- Evaluation on public questionnaire templates (CAIQ / CAIQ-Lite) plus
  a synthetic/de-identified knowledge library and SME-labelled test
  cases.

## Explicitly post-MVP — do not build without an explicit ask

- Production-grade privacy/legal drafting or legal advice.
- Full ISO/IEC 27001, SOC 2, GDPR, HIPAA, NIST control mapping as an
  **automated decision layer** (FR12 — framework mapping is allowed
  only as a human-confirmed *suggestion* after finalization, per
  `specs/01-architecture.md`).
- Third-party vendor risk scoring.
- Live bidirectional integrations with questionnaire portals.
- Multilingual questionnaires.
- Enterprise SSO/SAML, advanced RBAC, regional production deployment.
- Autonomous model fine-tuning from reviewer edits without a curated
  approval process (the Approved-Edit Reuse Store is a versioned
  retrieval exemplar store, not a training loop).

If a task in this repo would touch any of the above, stop and confirm
scope with the user before implementing — see
`.cursor/rules/mvp-scope-guard.mdc`.

## Limitations to design around

- Real completed questionnaires and internal security evidence are
  confidential — early evaluation leans on public templates, synthetic
  documents, and explicitly permissioned pilot data (see `data/README.md`).
- Ground-truth answer quality needs security/GRC expertise; the gold
  test set will be small and high-quality rather than large and weak.
- PDF tables, spreadsheets, scans, and inconsistent formatting will
  produce ingestion errors independent of the LLM — don't let
  ingestion bugs get misdiagnosed as generation bugs.
- RAG can fail silently (evidence absent or not retrieved; verifier
  false confidence). Human escalation is a *safety mechanism*, not a
  fallback to remove once the model looks good.
- Model/API cost, rate limits, and latency bound how many
  self-checking/verification calls are affordable per question.

## Assumptions

- Users have legitimate access to what they upload.
- Pilot data is synthetic, de-identified, or explicitly permissioned.
- A security/GRC reviewer is available to build/adjudicate the gold
  evaluation set.
- English-first MVP; hosted LLM APIs are fine, a local model is optional.
- The tool assists preparation and evidence organization — it does not
  itself certify compliance or replace legal/audit judgment.
- Success thresholds below are initial acceptance targets and may be
  revised after pilot calibration (record the revision, don't silently
  change a number).

## What "done" means for the MVP

All "Must" priority FR/NFR success criteria in
`specs/14-requirements-traceability.md` pass on the frozen held-out
benchmark, baselines B0/B1/B2/P have been run under the same protocol
(`specs/11-evaluation-and-baselines.md`), and a pilot SME review
session has exercised the Reviewer Console end to end
(`specs/09-reviewer-console.md`).

## Read next

- `specs/01-architecture.md` for the pipeline shape.
- `specs/02-data-model.md` for the schemas everything below builds on.
- `specs/roadmap-24-week.md` for what should exist by which week.
