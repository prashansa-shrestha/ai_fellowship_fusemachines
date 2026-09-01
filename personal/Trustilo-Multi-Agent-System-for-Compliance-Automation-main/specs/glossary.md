# Glossary

Kept short and specific to this project — general ML/RAG terminology
you already know from the lit review isn't repeated here, only the
terms used in a Trustilo-specific way.

- **Groundedness** — the property that every claim in an answer is
  entailed by its cited evidence. Trustilo's primary safety property
  (NFR1); distinct from "sounds plausible."
- **Abstention** — an `Answer` with `abstained=True`: the correct
  output when evidence is insufficient. Treated as a success, not a
  failure, in evaluation.
- **Tenant / customer namespace** — the isolation boundary
  (`tenant_id`) between different customers' evidence and questions.
  Never conflate with "user" — a tenant can have many reviewers.
- **Evidence freshness** — whether a cited `EvidenceChunk`'s version is
  still within its validity window at the time an answer is finalized.
- **Escalation** — routing an answer to a human reviewer instead of
  auto-finalizing it, based on a confidence/risk decision with
  explicit reason codes (NFR9).
- **Hard negative** — a deliberately constructed test case with
  evidence removed, contradicted, or made stale, used to test whether
  Verification/Escalation actually catch failures rather than just
  passing easy questions.
- **Baseline (B0/B1/B2/P)** — see `specs/11-evaluation-and-baselines.md`.
  Always refer to these by ID, not by informal names, to keep eval
  reports unambiguous.
- **CAIQ / CAIQ-Lite** — Cloud Security Alliance's Consensus
  Assessments Initiative Questionnaire; the primary public
  questionnaire source for the benchmark. CAIQ v4.1 has 283 questions
  across 17 domains aligned to CCM v4.1's 207 controls; CAIQ-Lite has
  138 questions across the same 17 domains.
- **CCM** — Cloud Controls Matrix, the control framework CAIQ
  questions are aligned to.
- **NIST CSF 2.0** — public framework with six functions (Govern,
  Identify, Protect, Detect, Respond, Recover); used only for the
  post-MVP Framework Mapping extension, not the MVP loop.
- **Approved-Edit Reuse Store** — where reviewer-approved edits become
  new retrievable evidence (FR11). Not a fine-tuning mechanism.
- **Framework Mapping** — post-MVP feature (FR12) suggesting
  compliance-framework references after an answer is finalized; starts
  as a human-confirmed suggestion, never an automated decision.
