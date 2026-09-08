# 13 — Tech Stack & Repo Layout

Status: living document. Source: `report/main.tex` §VIII (candidate
stack table) — this file turns "candidate" into a concrete default
and records the reasoning, so the choice is easy to revisit instead
of implicit.

## Decisions and rationale

| Layer | Default | Why |
|---|---|---|
| Backend/API | Python 3.11+, FastAPI | Async-native (matters for concurrent LLM/retrieval calls), Pydantic-native request/response models reuse the schemas in `common/schemas.py` directly. |
| Orchestration | LangGraph-style persisted state graph | The paper's own architecture diagram labels the Orchestrator node "State Graph" — this is a direct match, and it gives per-node retry/checkpoint semantics for free instead of hand-rolling them. A hand-rolled state machine over Postgres is a legitimate alternative if the team wants less framework dependency; if you switch, update this file and `specs/03-orchestrator.md`'s retry section accordingly. |
| Deployment shape | **Modular monolith**, not microservices | Three engineers, 24 weeks, "ordinary development machines are sufficient" per the paper's Resources section. Separate deployables per agent add operational overhead (service discovery, network calls, separate CI) with no MVP-stage benefit — NFR7's "replaceable" requirement is satisfied by clean package boundaries in `src/trustilo/`, not by separate processes. Revisit post-MVP if there's an actual scaling reason to. |
| Retrieval store | PostgreSQL + `pgvector` (dense) + Postgres full-text search / `tsvector` (sparse) | One database for both halves of hybrid retrieval keeps local dev and the eval harness simple — no separate search cluster to stand up for a 24-week project. Swap in OpenSearch/Elasticsearch later if lexical quality is the bottleneck; the retrieval interface in `specs/05-retrieval.md` doesn't change either way. |
| Parsing | `openpyxl`/`pandas` (XLSX/CSV), `pdfplumber` (PDF text/tables), OCR fallback only when needed | Matches the paper's parsing row; OCR is explicitly a fallback, not the default path, since most CAIQ-style PDFs are text-native. |
| LLM layer | Provider-abstracted client (`common/llm_provider.py`) wrapping Anthropic/OpenAI-compatible SDKs | NFR7 explicitly requires no hard dependency on one LLM vendor. Stronger model for drafting/verification, a smaller/cheaper model where classification is sufficient — configurable per `ExperimentConfig`. |
| Evidence storage | Local filesystem or S3-compatible object store (e.g. MinIO for dev) for source files; Postgres for metadata | Matches the paper's evidence-storage row; object store choice is swappable without touching the metadata schema. |
| Reviewer console | React (Vite) SPA calling the FastAPI backend, or FastAPI+HTMX if the team wants to minimize frontend surface | See `specs/09-reviewer-console.md` — kept deliberately lightweight. |
| Evaluation | Fixed JSONL/DB benchmark + `ExperimentConfig` IDs + the `trustilo-eval-metrics` skill | See `specs/11-evaluation-and-baselines.md`. |
| Observability | `structlog` structured logs; latency/token/cost fields on every LLM/retrieval call | Feeds NFR8 directly; don't add a heavyweight tracing stack before it's needed. |

## Repo layout

```
trustilo/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── report/
│   └── main.tex                  # the AIF submission — see .cursor/skills/aif-report-sync
├── specs/                        # this directory
├── src/trustilo/
│   ├── common/                   # schemas.py, llm_provider.py, config.py
│   ├── orchestrator/
│   ├── intake/
│   ├── retrieval/
│   ├── drafting/
│   ├── verification/
│   ├── escalation/
│   ├── knowledge_library/        # ingestion + versioning of evidence documents
│   ├── export_audit/             # FR10/FR11/NFR3
│   └── evaluation/                # harness that calls the eval skill
├── apps/
│   └── reviewer-console/
├── data/                         # synthetic corpus, benchmark splits — see data/README.md
└── tests/
    ├── unit/                     # one test module per src/trustilo/<stage>
    └── eval/                     # baseline/ablation runner + fixtures
```

Each `src/trustilo/<stage>/` package has its own nested `AGENTS.md`
with the FR/NFR IDs it owns and its I/O contract — Cursor picks these
up automatically when you're editing files inside that folder, so the
root `AGENTS.md` doesn't need to repeat per-stage detail.

## Local dev environment (starting point)

- Python 3.11+, `pip install -e ".[dev]"` (or `uv sync`).
- PostgreSQL 16+ with the `pgvector` extension enabled.
- `.env` populated from `.env.example` with LLM provider keys and a
  local `DATABASE_URL` — never commit a real `.env`.
- `pytest tests/unit` should pass with zero external services once the
  schemas are in place (they're pure Pydantic models, no DB needed for
  those tests).
