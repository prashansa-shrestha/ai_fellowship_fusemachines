# Trustilo Phase 1: Intake and Classification

Phase 1 turns a small questionnaire into predictable `Question` records. It supports plain UTF-8 text,
UTF-8 CSV, and the active worksheet in an XLSX file. PDF is deliberately deferred and raises a clear
`NotImplementedError` instead of pretending that extraction succeeded.

## What happens

`parse(raw_file, source_format, tenant_id)` reads questions in source order. Plain text treats each non-empty
line as a question. CSV and XLSX find common question headers such as `Question` or `Question Text` without
regard to letter case, and retain an optional `Section` or `Category` column. Blank rows are skipped. CSV and
XLSX questions keep their physical row number, including the header row, so a later export can align an answer
with the original questionnaire.

The original question cell or line is stored in `raw_text`. A second value, `normalized_text`, collapses repeated
spaces, tabs, and line breaks without changing words or punctuation. Stable hash-based IDs are derived from the
tenant, format, exact input bytes, and question location. Parsing identical input twice therefore produces the
same IDs.

For example, `"Do you  require\tMFA?"` remains unchanged in `raw_text` and becomes
`"Do you require MFA?"` in `normalized_text`.

`classify(question)` returns a new `Question` instead of modifying the input. Small, readable keyword rules assign
a broad security domain such as `identity_and_access_management` and an expected answer shape such as `yes_no`,
`frequency`, `numeric`, or `free_text`. These rules make a useful supervisor demo because every result is easy to
trace, but they are a baseline—not a claim of production classification accuracy.

## Limits

- PDF parsing is not part of this checkpoint.
- XLSX parsing uses the active worksheet and expects headers in its first row.
- CSV and XLSX rows containing other data but no textual question raise an explicit error.
- Duplicate detection, novelty scoring, the complete CCM taxonomy, and benchmark accuracy validation remain
  future FR2 work. No success threshold is claimed yet, so FR1 and FR2 remain `in progress`.

## Verification

Run:

```bash
pytest -q tests/unit/test_schemas.py tests/unit/test_intake.py
ruff check src/trustilo/intake tests/unit/test_intake.py
```

The first command runs the canonical schema tests plus focused intake tests. The second checks the new Python code
for style and common mistakes. The tests cover normalization, deterministic IDs, CSV/XLSX source row preservation,
section retention, explicit PDF deferral, malformed-row errors, and non-mutating classification.

# Trustilo Phase 2: Tenant-Isolated Evidence Retrieval

Phase 2 adds a small in-memory evidence index for a supervisor-friendly local demo. It is deliberately not the
production PostgreSQL, pgvector, or hybrid dense-plus-sparse retriever described in the full specification. Its job
is to make the retrieval contract and its most important security boundary executable before those services exist.

## What happens

`InMemoryEvidenceIndex(chunks)` takes a defensive snapshot of canonical `EvidenceChunk` objects and groups them by
tenant immediately. A search checks that the supplied `tenant_id` matches the `Question.tenant_id`, selects only
that tenant's bucket, removes evidence that is not active at the requested time, and only then ranks candidates.
It never ranks a global list and filters afterward. Inputs and returned chunks are deep-copied, so later mutation
cannot move stored evidence into another tenant or modify the index.

`index.search(question, tenant_id, top_k, revised_query=None, as_of=None)` ranks case-insensitive word tokens. Common
question scaffolding words such as “do”, “you”, and “what” are ignored when content words are available. More query
terms covered is better, repeated useful overlap helps, and the complete content-word phrase receives the strongest
signal. Evidence IDs and provenance break exact ties, making results repeatable regardless of insertion order.
Chunks with no useful overlap are omitted rather than used to fill `top_k`.

For example, a question about “backup testing frequency” ranks a chunk containing all three terms above one that
only mentions backups. If Verification retries with `revised_query="hardware MFA production database access"`, that
text fully replaces the original backup question for ranking; it is not appended to it.

By default, the current UTC time is used for version filtering. An evidence chunk is included only when
`valid_from <= as_of <= valid_until`; a missing boundary is open-ended. Both boundaries are inclusive. Tests and
repeatable demos should pass an explicit timezone-aware `as_of` value. Expired and not-yet-valid chunks are excluded.

## Limits

- Ranking is an explainable lexical baseline, not FR4's production dense+sparse hybrid with reranking.
- The in-memory index is process-local and is not a persistence or deployment-security boundary.
- Retrieval scores are internal ordering signals because the canonical `EvidenceChunk` schema has no score field.
- Audit events for the original and revised query belong to the future orchestrator/audit integration and are not
  persisted by this pure local retriever.
- Recall@10 has not been measured on the held-out gold set, and deployment encryption remains unimplemented.
  Therefore FR4 and NFR2 are only `in progress`, not implemented or verified.

## Verification

Run:

```bash
pytest -q tests/unit/test_schemas.py tests/unit/test_intake.py tests/unit/test_retrieval.py
python3 -m compileall -q src/trustilo/retrieval tests/unit/test_retrieval.py
git diff --check -- .
```

The first command runs schema, intake, and retrieval behavior tests. The second compiles the new Python files to
catch syntax/import problems without running the app. The third checks edited text for whitespace errors. Retrieval
tests cover adversarial same-content tenant isolation, explainable ranking, revised-query replacement, fixed-time
version filtering, `top_k` validation, deterministic ties, and mutation-resistant index snapshots.

# Trustilo Phase 3: Grounded Drafting and Independent Verification

Phase 3 turns retrieved evidence into a citation-safe draft, then checks that draft without trusting how it was
created. Both stages are deterministic local baselines, which keeps a supervisor demo quick and makes every result
easy to explain.

## What happens

`draft(question, evidence, max_claims=3)` accepts only canonical `Question` and `EvidenceChunk` objects. It first
checks that every chunk belongs to the question's tenant and that each `chunk_id` is unique. With no evidence it
returns a normal, explicit abstention. Otherwise, it creates at most `max_claims` claims in retrieval order. Each
claim is the chunk's text with whitespace collapsed—not an invented paraphrase—and has one citation containing the
exact chunk ID, document ID, and version. Answer, claim, and citation IDs are stable hashes of their content and
provenance. The answer remains `drafted`; this stage does not decide whether it should pass or escalate.

`check(answer, evidence, as_of=...)` independently rebuilds a tenant-scoped lookup from the supplied chunks. For
each claim it checks that the citation points back to the correct claim, resolves to a supplied chunk, matches the
chunk's document ID and version, and is a normalized passage of the cited evidence. It also reports explicit
clause-and-subject-local polarity conflicts such as “required” versus “optional” or the presence versus absence of
“not”. Negated equivalents such as “not optional” and “required” are not flagged as contradictions. Verification
also flags evidence that is expired or not yet valid at the requested time. The support score is simply
supported claims divided by total claims. Verification never edits a claim and this checkpoint never requests a
retrieval retry.

The canonical model currently has `contradiction_flags` and `freshness_flags`, but no general citation-error field.
For now, citation resolution and support issues use clear prefixes in `contradiction_flags`, such as
`unresolved_citation:`, `citation_version_mismatch:`, and `unsupported_claim:`. Actual polarity conflicts start with
`contradiction:`. This avoids changing the shared schema during a partial checkpoint.

For example, suppose the supplied chunk says `Privileged access requires MFA.` Drafting produces that exact claim
and a citation to the chunk's real document and version. Verification resolves the citation and returns a support
score of `1.0`. If someone injects the claim `Privileged access does not require MFA.` while leaving the same
citation attached, Verification gives that claim no support and emits both unsupported and negation-contradiction
flags. If no chunks were supplied, Drafting creates a claim-free abstention and Verification returns `1.0` with
`abstention:no_claims_to_verify`; here `1.0` means no unsupported material claim was emitted, not that the question
was answered. The shared schema also permits an abstention to carry partial claims. Those are not automatically
safe: Verification emits `abstention:partial_claims_present` and checks every partial claim normally. An uncited
partial claim therefore scores `0.0` and receives an `uncited_claim:` issue.

## Limits

- Drafting copies conservative evidence passages; it does not yet compose a polished answer through the configured
  LLM-provider abstraction.
- Text support is contiguous whole-token containment after case and punctuation normalization, not semantic
  entailment. The small polarity rules are useful testable signals, not a complete contradiction detector.
- Prior approved-answer consistency, composite confidence, production requery behavior, escalation, and audit
  persistence are not connected yet.
- Freshness is reported separately from textual support, so stale evidence can still have a `1.0` support score and
  must be handled by the later escalation policy.
- FR5, FR6, FR7, and NFR1 remain `in progress` until their held-out success criteria are measured.

## Verification

Run the complete local checkpoint suite with:

```bash
pytest -q tests/unit
python3 -m compileall -q src/trustilo/drafting src/trustilo/verification tests/unit/test_drafting.py tests/unit/test_verification.py
git diff --check -- .
```

The first command runs all current unit tests. The second checks that the new modules and tests compile. The third
reports malformed whitespace in the working changes.
