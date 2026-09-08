# Trustilo checkpoint record

This file records the state of the partial local demo. “Done” means implemented and covered by local behavior tests;
it does not mean the specification's held-out accuracy, security, deployment, or usability targets have been met.

## Done across three checkpoints

1. **Intake and classification:** deterministic UTF-8 text, CSV, and active-sheet XLSX parsing; normalized text;
   stable source-aware identifiers; physical row and section retention; explicit PDF deferral; and a small
   transparent domain/answer-type classifier.
2. **Evidence retrieval:** a defensive in-memory snapshot grouped by tenant before ranking; active-version filtering;
   explainable lexical relevance; deterministic ties; revised-query replacement; and mutation-resistant results.
3. **Grounded drafting and verification:** safe abstention when no evidence is supplied; conservative evidence-text
   claims with exact stable citations; cross-tenant and ambiguous-chunk rejection; independent citation resolution,
   provenance, textual-support, polarity, and freshness checks; stable result IDs; and no automatic pass/escalate or
   requery decision.

The focused unit tests use synthetic data and include cross-tenant attempts, injected unsupported and mismatched
citations, explicit polarity conflicts, stale and future evidence, abstention, deterministic IDs, and mutation
checks. Requirement rows remain `in progress` where the real success criterion still needs benchmark or deployment
evidence.

## Left to do

- PDF questionnaire extraction.
- A stronger classification taxonomy, duplicate/novelty detection, and classification benchmarks.
- Production PostgreSQL storage, tenant-filtered hybrid dense+sparse retrieval, embeddings, reranking, versioned
  knowledge ingestion, and immutable audit logs.
- LLM-provider-backed grounded drafting with structured output while preserving exact citation guarantees.
- Production-grade semantic verification, prior-approved-answer consistency, composite confidence, and the guarded
  one-shot retrieval requery.
- Escalation policy, human reviewer console, approved-edit reuse, and reviewer decision persistence.
- Persisted orchestration, retry/resume behavior, questionnaire export, and complete end-to-end audit reconstruction.
- Frozen evaluation datasets, baseline/ablation runs, target-metric validation, cost/latency measurement, and SME
  evaluation.
- Deployment security work including authentication/authorization, secrets handling, encryption, monitoring, and
  operational hardening.

## Checkpoint commit subjects

1. `checkpoint: add questionnaire intake and classification`
2. `checkpoint: add tenant-isolated evidence retrieval`
3. `(this checkpoint)` `checkpoint: add grounded drafting and verification`

No commit hash is recorded for the third checkpoint until the primary task creates that commit.
