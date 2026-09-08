# 09 — Reviewer Console

Status: living document. Owns: the "one review screen" success
criterion under **NFR6**, and the end-user requirement: *"As a
reviewer, I want the exact concern highlighted so that I can resolve
it without re-reading the full pipeline trace."*

## Scope (MVP)

A lightweight web UI, intentionally minimal — the paper's MVP
deliberately prioritizes the grounding/verification/escalation loop
over UI polish. No enterprise SSO/RBAC in MVP (that's post-MVP, see
`specs/00-overview-and-mvp-scope.md`); a single shared reviewer login
per pilot tenant is acceptable for now.

## What a single review screen must show

For one `ReviewTask`, in one view, without navigation:

- The question text (original + normalized).
- The drafted answer's claims, each with its cited evidence
  snippet(s), source document, and version/date.
- The `VerificationResult` that triggered escalation: support score,
  any contradiction/freshness flags.
- The `EscalationDecision.reason_codes` and human-readable reason,
  rendered as the headline of the screen, not buried below the answer.
- Actions: approve / edit / reject / request more evidence, each
  writing a `ReviewTask` resolution (`specs/08-escalation-and-review.md`).

## Success criterion

Pilot reviewers can approve/edit without consulting raw logs in ≥90%
of flagged cases (NFR6). If a reviewer has to go dig through backend
logs to understand why something was flagged, that's this spec's
failure, not the reviewer's.

## Recommended default implementation

A small React (Vite) single-page app calling the FastAPI backend
directly (no separate BFF needed at this scale), or — if the team
wants to spend even less engineering time on UI — a server-rendered
FastAPI + HTMX view. Either is fine; pick one and note the choice in
`specs/13-tech-stack-and-repo-layout.md`. Do not invest in a design
system, multi-role permissions, or notifications for MVP — those are
signs of scope creep into post-MVP territory.

## Explicitly out of scope for MVP

- Multi-role RBAC, SSO.
- Notification/assignment routing beyond a simple queue.
- Bulk-approve workflows (risks exactly the "automation bias" failure
  mode called out in the lit review — reviewers over-trusting polished
  output. Keep review deliberately one-at-a-time for MVP.)
