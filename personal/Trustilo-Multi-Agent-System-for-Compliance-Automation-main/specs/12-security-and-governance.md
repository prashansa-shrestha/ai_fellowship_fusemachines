# 12 — Security, Auditability & Data Governance

Status: living document. Source: `report/main.tex` §VII. Owns
**NFR2** in full; cross-references NFR3 (see
`specs/10-export-audit-feedback.md`).

Trustilo handles sensitive security-posture information. Platform
security is a product requirement here, not an afterthought bolted on
later — treat every item below as MVP scope, even though the paper
frames some of it as "would require a separate threat model" for a
real production deployment.

## Required for MVP

- **Tenant/customer namespace enforcement before retrieval or storage
  access** — see `specs/05-retrieval.md` for the concrete
  implementation rule and `.cursor/rules/tenant-isolation-security.mdc`.
- **Encryption in transit and at rest** in the intended deployment
  design (document the design even if the academic prototype runs
  on a single dev machine without real TLS termination — the design
  doc is the deliverable, not necessarily a hardened deployment).
- **Least-privilege service credentials** — the retrieval service
  shouldn't hold write credentials it never uses, the reviewer console
  backend shouldn't hold raw LLM provider keys directly, etc.
- **Secrets management** — no secrets in source control, ever, even in
  a "just for the demo" branch. Use `.env` (git-ignored, see
  `.env.example`) for local dev; document the intended secret manager
  for anything beyond that.
- **Versioned evidence with source/owner/date** — this is FR3, cross-
  referenced here because it's also a governance control, not just a
  retrieval-quality feature.
- **Immutable/append-only audit records for key decisions** — see
  `specs/03-orchestrator.md` / `specs/10-export-audit-feedback.md`.
- **Configurable retention/deletion for test data** — pilot and
  synthetic data need a documented deletion path, not just a database
  no one ever cleans.
- **Prompt-injection defenses** — uploaded questionnaires and evidence
  documents are untrusted content. Nothing extracted from them should
  be interpreted as an instruction to the drafting/verification
  models; it supplies facts to cite, nothing else. Concretely: never
  concatenate raw document text into a system/instruction prompt
  segment — keep it in a clearly-delimited "evidence" context block,
  and don't let extracted text influence which tools/functions get
  called.

## Acceptance test

Adversarial tenant-isolation tests (seed two tenants, query as one,
assert zero leakage) must show **zero cross-tenant retrievals** — this
is NFR2's literal, non-negotiable success criterion. This test suite
should run in CI on every change that touches retrieval or storage
code, not just before a milestone demo.

## Framework references (for post-MVP mapping only)

NIST CSF 2.0 is organized around six functions — Govern, Identify,
Protect, Detect, Respond, Recover — and is a reasonable public mapping
taxonomy when Framework Mapping (FR12) is eventually built. CSA
CAIQ/CCM is the primary questionnaire-shaped artifact this project
targets for the MVP benchmark itself (see
`specs/11-evaluation-and-baselines.md`). Proprietary/licensed
standards content must only be stored/used per its license — the
academic prototype should prefer identifiers and public descriptions
over reproducing licensed control text.

## Explicitly deferred (would need a real threat model first)

Full production deployment hardening, regional data residency,
enterprise SSO/SAML, and formal third-party security review are out of
scope for this academic prototype — see
`specs/00-overview-and-mvp-scope.md`. Don't let "we should harden this
properly" become a reason to skip the MVP-required controls above;
they're a floor, not the ceiling.
