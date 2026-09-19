# W16 Agentic Evaluation Report

Live harness run on `gemini-2.5-flash`. First 4 cases completed; last 3 hit **API 429 quota** before the agent could run (not agent logic failures). Failure-injection tool behavior was verified offline via `eval/offline_checks.py` (PASS).

Cases run: **7**
- Task completion rate: **4/7** (57%) — **4/4** among cases that reached the model
- Tool-call correctness: **4/7** (57%) — **4/4** among cases that reached the model
- Trajectory length: mean=1.3, min=0, max=4 (zeros = quota exceptions)
- Tokens / query: mean=7103, min=0, max=43472

## Per-case results

| Case | Mode | Done | Tools OK | Iters | Tokens | Stop | Failure |
|------|------|------|----------|-------|--------|------|---------|
| simple_lookup | multi_agent | True | True | 2 | 2657 | verified | — |
| cross_week_compare | multi_agent | True | True | 4 | 43472 | verified | — |
| missing_topic | multi_agent | True | True | 2 | 2868 | verified | — |
| ambiguous_compare | multi_agent | True | True | 1 | 726 | ask_clarification | — |
| failure_tool_unavailable | multi_agent | False | False | 0 | 0 | exception | hard |
| failure_malformed_retrieval | multi_agent | False | False | 0 | 0 | exception | hard |
| single_agent_baseline | single_agent | False | False | 0 | 0 | exception | hard |

## Multi-agent vs single-agent token cost

Multi-agent `simple_lookup`: **2657** tokens (researcher 1929 + verifier 728). Single-agent baseline did not run (429 quota), so Δ is unavailable from this run.

## Failure log

- **failure_tool_unavailable** / **failure_malformed_retrieval** / **single_agent_baseline** [hard — harness/infra]: Gemini `429 RESOURCE_EXHAUSTED` after retries; agent never started. Not an agent trajectory failure.

## Failure-injection notes

- Live injection cases did not execute (quota). Offline: `tool_unavailable` and `malformed_retrieval` both return explicit error/invalid payloads and mark `ok=False` (`eval/offline_checks.py` PASS) — the agent is instructed to escalate rather than invent content when those strings appear.

## Taxonomy reminder (as applied)

- **Hard failure**: wrong tool path or capped out without a usable grounded answer; or injection case answered confidently from invalid evidence.
- **Soft failure**: recoverable miss (e.g. escalated/clarified when a direct grounded answer was expected).
- **Cascading soft failure**: early weak retrieval/proposal caused verifier retries that then exhausted the budget.
