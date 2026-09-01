# 07 — Verification

Status: living document. Owns: **FR7** (verification), **H3**, **H5**.

## FR7 — Verification

Independently check entailment/support, contradiction, evidence
freshness, and consistency against prior approved answers.

- **Success criterion:** detect ≥90% of deliberately injected
  unsupported/contradictory test answers (from the hard-negative test
  set — see `specs/11-evaluation-and-baselines.md`).
- **"Independently" is load-bearing.** The verifier must re-derive its
  judgment from the claim text and the cited evidence text — it must
  not simply ask "is the drafter confident?" or echo the drafter's own
  self-report. (This is the Chain-of-Verification lesson from the lit
  review: context-separated verification catches what echoing a draft
  doesn't.) In practice: give the verifier the claims + evidence, not
  the drafter's reasoning trace.
- Checks to run per claim: (a) is it entailed by the cited evidence
  text, (b) does it contradict other cited or nearby evidence, (c) is
  the cited evidence still within its validity window, (d) does it
  contradict a prior *approved* answer for a similar question.

## The one-shot retry

If support is weak because retrieval likely missed the right evidence
(not because evidence doesn't exist), Verification may emit exactly
one `requested_requery` with a `requery_query` string, sent back to
Retrieval (`specs/01-architecture.md`, `specs/05-retrieval.md`). After
that cycle, Verification must reach a decision — pass or escalate,
no second retry. Log both attempts on the audit trail so the error
taxonomy can tell "fixed by retry" from "still failed after retry"
apart.

## Confidence signal (feeds Escalation, H5)

Verification outputs a composite signal — not just a single number —
combining retrieval-side features (e.g. top-score margin, number of
supporting chunks) and verifier-side features (support score,
contradiction/freshness flags). H5 specifically claims this composite
beats thresholding the drafter's own self-reported confidence, so:
**don't let Escalation threshold on drafter confidence alone** — that
would make H5 untestable by construction.

## Interface

```
verification.check(answer: Answer, evidence: list[EvidenceChunk], prior_approved: list[Answer]) -> VerificationResult
```

`VerificationResult.requested_requery` is `None` on the second pass no
matter what — the Orchestrator enforces the one-retry cap
independently of what Verification asks for, as a belt-and-suspenders
guard against an infinite loop bug.

## What NOT to do here

- Don't let Verification silently "fix" a claim by rewriting it — its
  job is to judge and flag, not to edit. Rewriting belongs to the
  human reviewer (or, for the retry path, to a fresh Drafting call
  against better evidence).
