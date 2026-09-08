# 08 — Escalation & Human Review

Status: living document. Owns: **FR8** (confidence/escalation),
**FR9** (human review), **NFR6** (usability), **NFR9** (explainability).

## FR8 — Confidence and escalation

Combine retrieval/verifier signals into a confidence/risk decision;
create review tasks below threshold.

- **Success criteria:** needs-review recall ≥90%; precision target
  ≥60% during pilot (i.e. it's fine to over-flag somewhat early on —
  it is not fine to under-flag a genuinely risky answer).
- **Thresholds are calibrated on the development split only, then
  frozen before the held-out test run.** Changing a threshold after
  seeing test-set results invalidates the evaluation — see
  `.cursor/rules/eval-benchmark-integrity.mdc`.
- Escalation triggers (non-exhaustive, extend via reason codes, not by
  adding untracked special cases): missing evidence, contradiction
  detected, evidence stale, verifier disagreement/low support score,
  novel question with no similar approved precedent.

## NFR9 — Explainability

Every `EscalationDecision` with `decision == "escalate"` must carry a
**non-empty `reason_codes` list** (machine-readable, e.g.
`MISSING_EVIDENCE`, `CONTRADICTION`, `STALE_EVIDENCE`,
`LOW_VERIFIER_SUPPORT`, `NOVEL_QUESTION`) *and* a human-readable
explanation string. Both are required — the reason codes make
escalation reasons countable for the error taxonomy and dashboards;
the human-readable string is what the reviewer actually reads.

## FR9 — Human review

Reviewer can approve, edit, reject, or request more evidence; the
result becomes the authoritative final response.

- **Success criterion:** all reviewer decisions are persisted and
  reflected in export (`specs/10-export-audit-feedback.md`).
- A reviewer decision always wins over any automated signal — once a
  human has ruled on a `ReviewTask`, the system does not re-run
  verification or second-guess the outcome.
- "Request more evidence" is a legitimate outcome distinct from
  reject — it should route back toward evidence upload/ingestion, not
  just close the task unresolved.

## NFR6 — Usability

Review work should be concentrated on flagged items; a reviewer should
be able to resolve a flagged answer from one screen without consulting
raw logs, in ≥90% of flagged cases in pilot usability testing. See
`specs/09-reviewer-console.md` for what "one screen" needs to contain.

## Interface

```
escalation.decide(answer: Answer, verification: VerificationResult) -> EscalationDecision
review.resolve(task: ReviewTask, decision: Literal["approve","edit","reject","request_evidence"], corrected_answer: Answer | None) -> Answer
```

## Test protocol note

Because thresholds are frozen before the test run, write the
threshold-calibration step as its own script/command
(`/run-baseline` in `.cursor/commands/`) that operates only on the dev
split, and make it structurally impossible for that script to touch
the frozen test set — read from separate paths, don't rely on a filter
flag someone could forget to pass.
