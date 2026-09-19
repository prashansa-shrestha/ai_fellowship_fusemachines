#!/usr/bin/env python3
"""From-scratch evaluation harness for the W16 agentic feature.

Measures:
  - task completion rate
  - tool-call correctness (expected tools present + valid args when searchable)
  - trajectory length (iterations)
  - token usage (and multi- vs single-agent comparison when both run)
  - failure log with hard / soft / cascading soft classification

Usage (from task1_ai_assistant/):
  python -m eval.harness
  python -m eval.harness --case simple_lookup
  python -m eval.harness --out eval/results/report.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Allow `python -m eval.harness` from task1_ai_assistant/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402
from app.agent import run_agentic_chat  # noqa: E402
from app.rag import RagIndex  # noqa: E402
from eval.cases import CASES, EvalCase  # noqa: E402


@dataclass
class CaseResult:
    case_id: str
    query: str
    task_completed: bool
    tool_correct: bool
    trajectory_length: int
    tokens_total: int
    tokens_by_agent: dict = field(default_factory=dict)
    stopped_reason: str = ""
    mode: str = ""
    failure_class: str | None = None  # hard | soft | cascading_soft | None
    failure_notes: str = ""
    answer_preview: str = ""
    tool_log: list = field(default_factory=list)
    elapsed_sec: float = 0.0
    inject_failure: str | None = None


def _tool_correctness(case: EvalCase, result) -> bool:
    if not case.expected_tools:
        return True
    names = [t["name"] for t in result.tool_log]
    for needed in case.expected_tools:
        if needed not in names:
            return False
    # Valid args: search calls must include non-empty query
    for t in result.tool_log:
        if t["name"] == "search_course_materials":
            q = (t.get("args") or {}).get("query", "")
            if not isinstance(q, str) or not q.strip():
                return False
        if t["name"] == "load_skill":
            s = (t.get("args") or {}).get("skill_name", "")
            if not isinstance(s, str) or not s.strip():
                return False
    return True


def _classify_failure(case: EvalCase, result, task_ok: bool, tool_ok: bool) -> tuple[str | None, str]:
    if task_ok and tool_ok:
        return None, ""

    # Cascading soft: early soft mistake leads to later hard-looking failure
    # e.g. bad first search → verifier fails → max_verify or empty escalate
    verify_fails = getattr(result, "verification_failures", 0)
    if (
        not task_ok
        and verify_fails >= 1
        and result.stopped_reason in {"max_verify_failures", "max_iterations"}
    ):
        return (
            "cascading_soft",
            "Early weak evidence / soft miss cascaded into verify retries and stop.",
        )

    if not tool_ok and not task_ok:
        return "hard", "Wrong or missing tool selection and task not completed."

    if not tool_ok and task_ok:
        return "soft", "Task answer acceptable but tool selection/args off."

    if task_ok and not tool_ok:
        return "soft", "Unexpected: task ok tool not — treated soft."

    # task not ok, tools ok
    if case.inject_failure:
        return (
            "hard",
            "Failure-injection case: agent did not recognize invalid/unavailable evidence.",
        )

    if result.stopped_reason == "max_iterations":
        return "hard", "Hit iteration cap without a usable answer."

    if result.escalate_to_human or result.stopped_reason == "ask_clarification":
        # For cases that required a real answer, escalate is a soft miss
        return "soft", "Escalated or asked clarification instead of completing."

    return "soft", "Answer incomplete or success_check failed despite tools."


def run_case(rag: RagIndex, case: EvalCase) -> CaseResult:
    t0 = time.time()
    try:
        result = run_agentic_chat(
            rag,
            case.query,
            inject_failure=case.inject_failure,
            single_agent=case.single_agent,
        )
    except Exception as err:
        elapsed = time.time() - t0
        return CaseResult(
            case_id=case.id,
            query=case.query,
            task_completed=False,
            tool_correct=False,
            trajectory_length=0,
            tokens_total=0,
            stopped_reason="exception",
            mode="multi_agent" if not case.single_agent else "single_agent",
            failure_class="hard",
            failure_notes=f"Harness caught exception: {type(err).__name__}: {err}"[:400],
            answer_preview="",
            tool_log=[],
            elapsed_sec=round(elapsed, 2),
            inject_failure=case.inject_failure,
        )
    elapsed = time.time() - t0

    task_ok = bool(case.success_check(result)) if case.success_check else True
    tool_ok = _tool_correctness(case, result)
    fail_class, fail_notes = _classify_failure(case, result, task_ok, tool_ok)

    tokens = result.tokens or {}
    return CaseResult(
        case_id=case.id,
        query=case.query,
        task_completed=task_ok,
        tool_correct=tool_ok,
        trajectory_length=result.iterations,
        tokens_total=int(tokens.get("total_tokens") or 0),
        tokens_by_agent=dict(tokens.get("by_agent") or {}),
        stopped_reason=result.stopped_reason,
        mode=result.mode,
        failure_class=fail_class,
        failure_notes=fail_notes,
        answer_preview=(result.answer or "")[:280].replace("\n", " "),
        tool_log=result.tool_log,
        elapsed_sec=round(elapsed, 2),
        inject_failure=case.inject_failure,
    )


def render_report(results: list[CaseResult]) -> str:
    n = len(results)
    completed = sum(1 for r in results if r.task_completed)
    tool_ok = sum(1 for r in results if r.tool_correct)
    traj = [r.trajectory_length for r in results]
    toks = [r.tokens_total for r in results]

    lines = [
        "# W16 Agentic Evaluation Report",
        "",
        f"Cases run: **{n}**",
        f"- Task completion rate: **{completed}/{n}** ({100 * completed / n:.0f}%)",
        f"- Tool-call correctness: **{tool_ok}/{n}** ({100 * tool_ok / n:.0f}%)",
        f"- Trajectory length: mean={sum(traj)/n:.1f}, min={min(traj)}, max={max(traj)}",
        f"- Tokens / query: mean={sum(toks)/n:.0f}, min={min(toks)}, max={max(toks)}",
        "",
        "## Per-case results",
        "",
        "| Case | Mode | Done | Tools OK | Iters | Tokens | Stop | Failure |",
        "|------|------|------|----------|-------|--------|------|---------|",
    ]
    for r in results:
        lines.append(
            f"| {r.case_id} | {r.mode} | {r.task_completed} | {r.tool_correct} | "
            f"{r.trajectory_length} | {r.tokens_total} | {r.stopped_reason} | "
            f"{r.failure_class or '—'} |"
        )

    # Multi- vs single-agent token comparison
    multi = next((r for r in results if r.case_id == "simple_lookup"), None)
    single = next((r for r in results if r.case_id == "single_agent_baseline"), None)
    lines += ["", "## Multi-agent vs single-agent token cost", ""]
    if multi and single:
        delta = multi.tokens_total - single.tokens_total
        lines.append(
            f"Same query (`Week 14 intent routing`): multi-agent "
            f"**{multi.tokens_total}** tokens vs single-agent "
            f"**{single.tokens_total}** tokens "
            f"(Δ = {delta:+d}). "
            f"Verifier share on multi: {multi.tokens_by_agent}."
        )
    else:
        lines.append("Baseline pair not both present in this run.")

    fails = [r for r in results if r.failure_class]
    lines += ["", "## Failure log", ""]
    if not fails:
        lines.append("No failures recorded.")
    else:
        for r in fails:
            lines.append(
                f"- **{r.case_id}** [{r.failure_class}]: {r.failure_notes} "
                f"(stop={r.stopped_reason})"
            )
            lines.append(f"  - preview: {r.answer_preview!r}")

    lines += [
        "",
        "## Failure-injection notes",
        "",
    ]
    inj = [r for r in results if r.inject_failure]
    if not inj:
        lines.append("No injection cases in this run.")
    else:
        for r in inj:
            recognized = r.task_completed
            lines.append(
                f"- `{r.inject_failure}` on **{r.case_id}**: "
                f"{'recognized / degraded safely' if recognized else 'DID NOT handle safely'}; "
                f"escalate-or-honest success_check={recognized}."
            )

    lines += ["", "## Taxonomy reminder (as applied)", ""]
    lines.append(
        "- **Hard failure**: wrong tool path or capped out without a usable grounded answer; "
        "or injection case answered confidently from invalid evidence."
    )
    lines.append(
        "- **Soft failure**: recoverable miss (e.g. escalated/clarified when a direct "
        "grounded answer was expected)."
    )
    lines.append(
        "- **Cascading soft failure**: early weak retrieval/proposal caused verifier "
        "retries that then exhausted the budget."
    )
    lines.append("")
    return "\n".join(lines)


def load_rag() -> RagIndex:
    index = RagIndex()
    faiss_path = config.INDEX_DIR / "index.faiss"
    if faiss_path.exists():
        index.load(config.INDEX_DIR)
    else:
        index.build(config.CORPUS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        index.save(config.INDEX_DIR)
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W16 agentic eval harness")
    parser.add_argument("--case", help="Run a single case id", default=None)
    parser.add_argument(
        "--out",
        default=str(ROOT / "eval" / "results" / "report.md"),
        help="Markdown report path",
    )
    parser.add_argument(
        "--json",
        default=str(ROOT / "eval" / "results" / "results.json"),
        help="JSON results path",
    )
    args = parser.parse_args(argv)

    if not config.GEMINI_API_KEY:
        print("GEMINI_API_KEY missing — set it in ../.env", file=sys.stderr)
        return 2

    cases = CASES
    if args.case:
        cases = [c for c in CASES if c.id == args.case]
        if not cases:
            print(f"Unknown case id: {args.case}", file=sys.stderr)
            return 2

    print(f"Loading RAG index from {config.INDEX_DIR} …")
    rag = load_rag()
    print(f"Indexed chunks: {len(rag.chunks)}")

    results: list[CaseResult] = []
    for i, case in enumerate(cases):
        if i > 0:
            # Free-tier Gemini RPM is low; space cases out.
            time.sleep(25)
        print(f"\n=== {case.id} ===\n{case.query[:100]}…", flush=True)
        cr = run_case(rag, case)
        results.append(cr)
        print(
            f"done={cr.task_completed} tools={cr.tool_correct} "
            f"iters={cr.trajectory_length} tokens={cr.tokens_total} "
            f"stop={cr.stopped_reason} fail={cr.failure_class}",
            flush=True,
        )

    report = render_report(results)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    json_path = Path(args.json)
    json_path.write_text(
        json.dumps([asdict(r) for r in results], indent=2),
        encoding="utf-8",
    )
    print("\n" + report)
    print(f"\nWrote {out_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
