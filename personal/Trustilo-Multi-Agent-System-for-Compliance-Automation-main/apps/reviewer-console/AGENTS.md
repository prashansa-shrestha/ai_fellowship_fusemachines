# AGENTS.md — reviewer-console

Owns: the human side of **FR9** and the "one review screen" success
criterion in **NFR6**. Full spec: `../../specs/09-reviewer-console.md`.

- This is deliberately a thin client over the FastAPI backend's
  `ReviewTask` endpoints — no independent business logic here. The
  authoritative decision path lives in `src/trustilo/escalation/`.
- A single `ReviewTask` view must show, without navigation: the
  question, the drafted claims with their cited evidence and
  source/version, the verifier's flags, and the escalation reason
  codes as the headline — see the full checklist in the spec before
  building a screen that's missing one of these.
- No SSO/RBAC, no notification system, no bulk-approve in MVP — see
  `../../specs/00-overview-and-mvp-scope.md`. If asked to add any of
  these, confirm it's an intentional post-MVP request first.
- Framework choice (React/Vite vs. FastAPI+HTMX) is not fixed — see
  `../../specs/13-tech-stack-and-repo-layout.md`. Pick one early and
  don't mix approaches within this app.
