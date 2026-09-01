# 05 — Retrieval

Status: living document. Owns: **FR4** (hybrid retrieval), **NFR2**
(tenant isolation happens here first), **H2**.

## FR4 — Hybrid retrieval

Retrieve evidence using dense semantic search plus sparse/lexical
signals, with optional re-ranking.

- **Success criterion:** Evidence Recall@10 ≥90% on the gold retrieval
  set (a set of question → gold-chunk-id mappings, held fixed for
  comparison across baselines).
- Default implementation: pgvector for dense (cosine/inner-product
  over chunk embeddings) + Postgres full-text search (`tsvector`) for
  lexical, combined via reciprocal rank fusion or a weighted score;
  optional cross-encoder re-rank on the fused top-N before truncating
  to top-k. See `specs/13-tech-stack-and-repo-layout.md` for why
  Postgres does double duty here instead of a separate lexical engine.

## Tenant isolation — this is where NFR2 is actually enforced

**The tenant filter is a `WHERE tenant_id = :tenant_id` clause applied
in the same query as the similarity search, not a post-hoc filter on
returned rows.** A retrieval function that fetches broadly and filters
in application code is a defect even if it happens to return the
right rows in testing — it's one refactor away from a cross-tenant
leak. Every retrieval code path needs an adversarial isolation test:
seed two tenants with overlapping content, query as tenant A, assert
zero chunks from tenant B ever leave the database layer. Target: zero
cross-tenant retrievals across all such tests (NFR2's literal
success criterion).

## Evidence-version filtering

Retrieval should be able to exclude superseded evidence versions (see
`specs/02-data-model.md`) from the candidate set, or at minimum
surface version/`valid_until` alongside every returned chunk so
Verification can do freshness checks without a second round-trip.

## Query revision entry point

Retrieval must accept an optional `revised_query` parameter distinct
from the original question text, used exactly once when Verification
requests a retry (`specs/01-architecture.md`, `specs/07-verification.md`).
Log both the original and revised query on the `AuditEvent` trail so
the error taxonomy can distinguish "retrieval never found it" from
"retrieval found it only after query revision."

## Interface

```
retrieval.search(
    question: Question,
    tenant_id: str,
    top_k: int,
    revised_query: str | None = None,
) -> list[EvidenceChunk]  # ranked, with score + version metadata attached
```

## Ablation hooks (`specs/11-evaluation-and-baselines.md`)

The retrieval module must support running as: dense-only, sparse-only,
hybrid-no-rerank, hybrid-with-rerank, and hybrid ± prior-approved-Q/A
retrieval — all via `ExperimentConfig.retriever_config`, not via
code branches you have to comment/uncomment. If adding a new retrieval
strategy, wire it through this config rather than hardcoding a choice.
