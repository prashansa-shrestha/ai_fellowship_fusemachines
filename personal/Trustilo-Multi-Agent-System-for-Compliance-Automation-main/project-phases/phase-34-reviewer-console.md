# Phase 34 — Reviewer console

**Feature branch:** `codex/feature-34-reviewer-console`  
**Depends on:** Phase 33  
**Traceability:** `specs/09-reviewer-console.md`; FR9, NFR6

## Goal

Build the minimal one-question-at-a-time reviewer interface required to resolve a flagged answer without reading raw logs.

## Implementation

- Record the chosen React/Vite or FastAPI/HTMX approach in the tech-stack spec.
- Show original/normalized question, claims, evidence snippets with source/version/date, verification flags, and escalation reasons in one view.
- Provide approve, edit, reject, and request-more-evidence actions with clear validation and success/error states.
- Keep SSO/RBAC, notifications, bulk approval, and design-system work out of scope.

## UI tests

- Component tests for all required fields, reason-code prominence, evidence expansion, editing, and action validation.
- Loading, empty, stale-task, server-error, and keyboard-accessibility cases.
- Verify raw logs are not required or exposed.

## Done when

A reviewer can understand and resolve one flagged task entirely from the specified screen.
