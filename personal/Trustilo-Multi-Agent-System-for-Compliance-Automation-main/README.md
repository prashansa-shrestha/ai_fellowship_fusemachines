# Trustilo — Cursor project scaffold

This is the engineering scaffold for **Trustilo**, the multi-agent
evidence-grounded security-questionnaire system described in
`report/main.tex` (your AIF requirement + literature review
submission). It's built to be opened directly in Cursor.

It does **not** contain the working product yet — Retrieval, Drafting,
Verification etc. are still empty packages. What it does contain is
everything needed to start building consistently as a three-person
team over the 24-week plan: specs, data schemas, coding rules, and a
few Cursor-native automations.

## Quickstart

1. Unzip this into a fresh git repo (or copy its contents into an
   existing one) and open the folder in Cursor.
2. Read `AGENTS.md` — it's the front door for both you and the agent.
3. Skim `specs/00-overview-and-mvp-scope.md` and
   `specs/roadmap-24-week.md` to see the shape of the whole project.
4. `pip install -e ".[dev]"` (or your preferred tool — `uv sync` works
   too) and `pytest tests/unit` to confirm the starter schemas import
   and pass.
5. Start on Week 1–4 of the roadmap: freeze the schemas (already
   drafted in `src/trustilo/common/schemas.py` — review and adjust
   them as a team), then build Intake/Classification against
   `specs/04-intake-classification.md`.

## How the pieces fit together

```
report/main.tex   ──  the "why" (your AIF submission)
specs/            ──  the "what" (engineering-ready requirements)
AGENTS.md (+nested) ── the "house rules" an AI agent reads automatically
.cursor/rules/    ──  narrow, always-or-conditionally loaded coding rules
.cursor/skills/   ──  packaged, scripted workflows (eval metrics, report sync)
.cursor/commands/ ──  one-off "/do-this-repeatable-thing" prompts
.cursor/agents/   ──  reviewer/auditor subagents for your *coding* workflow
src/trustilo/     ──  the actual product code (one package per pipeline stage)
```

If you're new to this workflow: rules are the things you want
enforced on (almost) every change; skills are workflows with real
logic behind them; commands are prompts you type `/like-this`;
subagents are specialists the main agent can hand off review/audit
work to so it doesn't have to hold everything in one context window.
None of this is required to use Cursor — it just makes a 3-person,
24-week, spec-heavy project much less likely to drift.

> **Version note:** Skills (`SKILL.md`) and Subagents
> (`.cursor/agents/`) are part of Cursor's newer Customize surface
> (2.4+). If your Cursor build predates that, it will still read
> `.cursor/rules/`, `.cursor/commands/`, and `AGENTS.md` normally —
> update Cursor to get the skills/subagents pieces too.

## Folder map

| Folder | Contents |
|---|---|
| `specs/` | 17 files: scope, architecture, data model, one file per pipeline stage, evaluation/baselines, security, tech stack, requirements traceability, 24-week roadmap, glossary |
| `report/` | Your existing `main.tex` AIF submission, unmodified |
| `src/trustilo/` | Python package skeleton: `common` (shared schemas/config), `orchestrator`, `intake`, `retrieval`, `drafting`, `verification`, `escalation`, `knowledge_library`, `export_audit`, `evaluation` |
| `apps/reviewer-console/` | Placeholder for the human reviewer UI |
| `data/` | Where the synthetic corpus and benchmark splits go — read the README there first |
| `tests/` | `unit/` for stage tests, `eval/` for the baseline/ablation harness |
| `.cursor/` | Rules, skills, commands, subagents (see below) |

## `.cursor/` contents at a glance

**Rules** (`.cursor/rules/*.mdc`)
- `00-project-context.mdc` — always-on: grounding, tenant isolation, auditability, MVP scope
- `data-model-and-versioning.mdc` — schema/versioning conventions
- `python-service-conventions.mdc` — typed, structured, idempotent stage code
- `llm-prompting-and-grounding.mdc` — structured output, citation, abstention rules for drafting/verification prompts
- `tenant-isolation-security.mdc` — hard rule on every retrieval/storage path
- `eval-benchmark-integrity.mdc` — frozen test set, standard metrics, logged cost/latency
- `mvp-scope-guard.mdc` — stops silent post-MVP scope creep

**Skills** (`.cursor/skills/*/SKILL.md`)
- `trustilo-eval-metrics` — real, dependency-light Python for every metric in `specs/11-evaluation-and-baselines.md`
- `aif-report-sync` — keeps `report/main.tex` consistent with implementation status without breaking LaTeX structure

**Commands** (`.cursor/commands/*.md`, type `/name` in Agent chat)
- `/new-pipeline-stage`, `/trace-requirement`, `/run-baseline`, `/write-ablation-report`, `/sync-report`

**Subagents** (`.cursor/agents/*.md`)
- `spec-compliance-auditor`, `groundedness-reviewer`, `tenant-isolation-auditor`, `eval-runner`

## Assumptions I made

The paper's tech-stack table is explicitly a *candidate* list, so I
picked one concrete, defensible option for each layer and wrote the
reasoning into `specs/13-tech-stack-and-repo-layout.md` — Python
monolith (not microservices) with FastAPI, LangGraph-style
orchestration, Postgres+pgvector for both dense and lexical retrieval,
and a provider-agnostic LLM client interface. Nothing about the
specs or rules depends on these choices being final — swap them and
update that one file.
