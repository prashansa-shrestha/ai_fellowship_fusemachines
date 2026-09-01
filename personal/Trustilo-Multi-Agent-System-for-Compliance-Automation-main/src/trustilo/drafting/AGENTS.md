# AGENTS.md — drafting

Owns: **FR5** (grounded drafting), **FR6** (citations), and is the
first of two packages the `groundedness-reviewer` subagent watches
closely (the other is `verification/`). Full spec:
`../../../specs/06-drafting.md`.

- The drafter receives only the evidence chunks Retrieval selected —
  never the full knowledge library, never "general knowledge" framed
  as evidence.
- Output is structured (`Answer`/`Claim`/`Citation` from
  `common/schemas.py`), not freeform text parsed after the fact.
- A `Claim` with zero citations is only valid when the whole `Answer`
  is `abstained=True` — this is enforced by a schema validator, but
  don't rely on the validator alone; the prompt itself should make
  abstention feel like a normal, correct, non-penalized outcome to the
  model, not a last resort.
- Don't let this package decide pass/escalate — that's
  Verification/Escalation's job (`specs/07-verification.md`,
  `specs/08-escalation-and-review.md`). Keep roles separated even when
  the same underlying model powers multiple stages.
- Self-consistency sampling is an explicit ablation, not a default —
  see `specs/11-evaluation-and-baselines.md` before adding it here.
