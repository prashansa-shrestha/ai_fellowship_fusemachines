# AGENTS.md — escalation

Owns: **FR8** (confidence/escalation), **FR9** (human review), **NFR9**
(explainability). Full spec:
`../../../specs/08-escalation-and-review.md`.

- Escalation thresholds are calibrated on the development split only,
  then frozen before any held-out test run — this package should make
  it structurally awkward to tune a threshold against test data (e.g.
  separate calibration script/path), not just rely on discipline.
- Every `EscalationDecision` with `decision == "escalate"` must carry
  non-empty `reason_codes` — enforced by a schema validator in
  `common/schemas.py`, but write the reason codes to actually be
  useful (specific, from the fixed vocabulary in the spec), not
  generic.
- A reviewer's decision on a `ReviewTask` is final — this package does
  not re-run verification or second-guess a human decision once made.
- "Request more evidence" is a distinct outcome from "reject" — route
  it back toward ingestion, don't collapse it into rejection.
