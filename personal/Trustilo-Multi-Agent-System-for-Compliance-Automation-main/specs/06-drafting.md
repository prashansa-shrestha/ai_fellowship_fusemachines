# 06 — Grounded Drafting

Status: living document. Owns: **FR5** (grounded drafting), **FR6**
(citation generation), **H1**. This is the single most safety-critical
stage in the system — see `.cursor/rules/llm-prompting-and-grounding.mdc`.

## FR5 — Grounded drafting

Generate a concise answer **only** from supplied evidence; return
"insufficient evidence" (an abstention) when support is absent.

- **Success criterion:** ≥95% claim-support precision for
  auto-finalized answers.
- The drafter receives *only* the evidence chunks Retrieval selected —
  never the full knowledge library, never "general knowledge" framed
  as if it were evidence. If the drafter wants to answer from
  something it wasn't given, that's an abstention, not a creative
  workaround.
- Output is **structured**, not freeform prose: a list of `Claim`
  objects, each either backed by ≥1 `Citation` or the whole `Answer`
  is marked `abstained=True` with an `abstain_reason`. Freeform prose
  that "sounds cited" but isn't machine-checkable against
  `EvidenceChunk` IDs does not satisfy FR6.

## FR6 — Citation generation

Attach passage/document references to material claims.

- **Success criterion:** 100% of auto-finalized answers include valid,
  traceable citations (i.e. every `citation.chunk_id` resolves to a
  real, tenant-scoped `EvidenceChunk`).
- A citation that doesn't resolve, or resolves to a chunk from a
  different tenant, is a bug at the schema-validation level (see
  `specs/02-data-model.md`), not something caught only in eval.

## Interface

```
drafting.draft(question: Question, evidence: list[EvidenceChunk]) -> Answer
```

`Answer.claims` is empty and `abstained=True` when evidence is
insufficient. The drafter must never be asked to also decide
pass/escalate — that's Verification/Escalation's job (separation of
roles, per the Self-Refine lesson in the lit review: separating
generator and critic roles helps even when it's the same base model).

## Prompting conventions

- Require structured output (JSON schema matching `Answer`/`Claim`) —
  don't parse free text with regex.
- Every claim must be traceable to specific evidence text, not a
  paraphrase-then-hope-it's-supported.
- Explicitly instruct the model that "I don't know" / abstention is a
  *correct*, rewarded answer when evidence is thin — this is easy to
  under-prompt and get an over-confident drafter by default.
- Treat all evidence text as data to cite, never as instructions
  (prompt-injection defense — `specs/12-security-and-governance.md`).

## What NOT to do here

- Don't let the drafter see prior escalation/reviewer history for
  *this* question (that would leak the answer). It may see prior
  **approved** Q/A pairs surfaced by Retrieval as evidence, like any
  other evidence chunk — that's intentional (FR11), not a leak.
- Don't add self-consistency sampling here by default — that's an
  explicit ablation (`specs/11-evaluation-and-baselines.md`), only
  used on borderline cases per the paper's design, not on every draft
  (cost/latency budget, NFR4/NFR8).
