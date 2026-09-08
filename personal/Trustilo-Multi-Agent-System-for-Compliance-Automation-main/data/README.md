# `data/`

## Rule 1: nothing confidential lives here

Real customer questionnaires and real customer evidence documents are
confidential (see `specs/00-overview-and-mvp-scope.md` Limitations and
`specs/12-security-and-governance.md`). Only synthetic, de-identified,
or explicitly permissioned pilot data belongs in this folder — and
even then, check `.gitignore` covers it before committing (it
currently ignores `data/pilot/` and `data/real-customer-*/` by
default; don't remove those entries casually).

## Intended layout

```
data/
├── synthetic_corpus/     # generated company profile + policy/evidence docs
│                         # with explicit, internally-consistent version dates
├── questionnaires/       # CAIQ / CAIQ-Lite question sets, and any
│                         # de-identified questionnaire shapes for
│                         # ingestion-format testing (specs/04-intake-classification.md)
├── hard_negatives/       # deliberately constructed cases: evidence
│                         # removed / contradicted / made stale
│                         # (specs/11-evaluation-and-baselines.md)
├── gold_labels/          # SME-labelled evidence-relevance, claim-support,
│                         # and "needs review" labels — dev split
├── benchmark_dev/        # frozen-ish development split (tunable)
└── benchmark_test/       # FROZEN held-out test split — see
                          # .cursor/rules/eval-benchmark-integrity.mdc
                          # before touching anything under this path
```

## Before adding real pilot data

If a pilot customer provides real (even partially redacted) evidence
or questionnaires, don't just drop it in `data/`. Confirm: is there
explicit permission for this specific use, is it stored under
`data/pilot/` (already git-ignored), and does it need a retention/
deletion plan per `specs/12-security-and-governance.md`? If any answer
is unclear, ask before committing anything.

## Building the synthetic corpus

See `specs/11-evaluation-and-baselines.md` (Hard Negatives) and
`report/main.tex` §III.C (Data Acquisition Methods) for what the
synthetic company profile and evidence set need to cover: internally
consistent policy statements, explicit version/effective dates so
freshness checks are testable, and deliberate contradictions/staleness
injected on a known subset so Verification's detection rate is
actually measurable.
