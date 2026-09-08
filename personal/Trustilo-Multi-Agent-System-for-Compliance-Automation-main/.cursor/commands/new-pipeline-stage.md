Scaffold a new Trustilo pipeline stage consistently.

Ask which stage this is (if not already clear from context) and
confirm it maps to one of the packages under `src/trustilo/`:
`orchestrator`, `intake`, `retrieval`, `drafting`, `verification`,
`escalation`, `knowledge_library`, `export_audit`, `evaluation`.

Then:

1. Read that package's nested `AGENTS.md` and the matching
   `specs/0N-*.md` file. Do not invent behavior that isn't in the
   spec — if something is genuinely underspecified, say so and
   propose an addition to the spec rather than silently deciding.
2. Create (or extend) the module with a clear function-based interface
   matching the "Interface" section of the spec, using the Pydantic
   models in `src/trustilo/common/schemas.py`.
3. Follow `.cursor/rules/python-service-conventions.mdc`: typed, async
   where it touches I/O, structured logging with `stage`/`question_id`/
   `tenant_id`, idempotent given persisted state.
4. Add a unit test in `tests/unit/` that exercises the stage's stated
   success criterion from the spec, using synthetic fixtures — not a
   trivial smoke test.
5. Update `specs/14-requirements-traceability.md`: set the relevant
   FR/NFR row(s) to `in progress` or `implemented` as appropriate.
6. Summarize what was built and which spec success criteria are and
   are not yet met.

Do not implement anything listed as post-MVP in
`specs/00-overview-and-mvp-scope.md` as part of this scaffold.
