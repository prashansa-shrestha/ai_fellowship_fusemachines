# AGENTS.md — verification

Owns: **FR7**. Full spec: `../../../specs/07-verification.md`.

- Must independently re-derive its judgment from claim text + cited
  evidence text. Never take the drafter's own confidence/reasoning as
  an input signal — that turns "independent" verification into an
  echo of the thing it's supposed to check.
- May request exactly one `requested_requery` back to Retrieval
  (`VerificationResult.requested_requery` + `requery_query` in
  `common/schemas.py`) — the Orchestrator enforces the one-cycle cap
  independently, but this package shouldn't ask for a second one
  either.
- Confidence output is a composite of retrieval-side and verifier-side
  features, not the drafter's self-reported confidence alone — H5 in
  `specs/00-overview-and-mvp-scope.md` specifically depends on this
  distinction being real, not cosmetic.
- Flags and judges; it does not rewrite claims. Rewriting belongs to a
  fresh Drafting call (after a requery) or to a human reviewer.
