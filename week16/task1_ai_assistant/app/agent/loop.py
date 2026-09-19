"""Explicit multi-agent loop: Researcher (tools) + Verifier (isolated check).

Stopping conditions:
- propose_answer + verifier PASS
- ask_clarification
- max iterations / max verification failures
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from .. import config
from ..net import ipv4_httpx_client
from ..rag import RagIndex
from .gemini_util import generate_with_retry
from .notes import EvidenceNotebook
from .tokens import TokenLedger
from .tools_agent import make_researcher_tools
from .verifier import run_verifier

RESEARCHER_SYSTEM = (
    "You are the Researcher agent for the Fusemachines AI Fellowship Course Assistant.\n"
    "Your job is to gather evidence with tools, then propose_answer OR ask_clarification.\n"
    "Never invent course facts. Prefer search_course_materials; refine the query if hits "
    "are weak or from the wrong week. For comparisons, load_skill('compare_course_options') "
    "first, then search each option (at most one search per option) before propose_answer.\n"
    "Budget: you have a small iteration limit — after 2–4 useful tool calls, prefer "
    "propose_answer (or ask_clarification) instead of more searching.\n"
    "Skill catalog (progressive disclosure — load full text only when needed):\n"
    "{skill_catalog}\n"
    "After each search you only see a short notebook digest (raw chunks were cleared).\n"
    "When evidence is enough, call propose_answer. If the question is ambiguous, "
    "call ask_clarification. If materials truly lack the answer, propose_answer with "
    "escalate_to_human=true."
)


@dataclass
class AgentTraceStep:
    iteration: int
    agent: str
    action: str
    detail: str = ""


@dataclass
class AgentResult:
    answer: str
    sources: list[str]
    escalate_to_human: bool
    provider_used: str = "gemini-agent"
    iterations: int = 0
    stopped_reason: str = ""
    clarification: str | None = None
    tokens: dict = field(default_factory=dict)
    tool_log: list[dict] = field(default_factory=list)
    trace: list[AgentTraceStep] = field(default_factory=list)
    verification_passes: int = 0
    verification_failures: int = 0
    mode: str = "multi_agent"


def _usage_config(tools: list, temperature: float, top_p: float, system: str):
    return types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        top_p=top_p,
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="ANY")
        ),
    )


def _extract_function_calls(response) -> list:
    calls = getattr(response, "function_calls", None)
    if calls:
        return list(calls)
    # Fallback: walk candidates
    out = []
    try:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                out.append(part.function_call)
    except Exception:
        pass
    return out


def _run_tool(name: str, args: dict, tool_map: dict[str, Any]) -> str:
    fn = tool_map.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(**(args or {}))
    except TypeError as err:
        return f"Invalid arguments for {name}: {err}"
    except Exception as err:
        return f"Tool {name} failed: {err}"


def run_agentic_chat(
    rag: RagIndex,
    message: str,
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    max_iterations: int | None = None,
    inject_failure: str | None = None,
    single_agent: bool = False,
    client: genai.Client | None = None,
) -> AgentResult:
    """Run the researcher(+verifier) loop for one user message."""
    temp = config.DEFAULT_TEMPERATURE if temperature is None else temperature
    top_p_v = config.DEFAULT_TOP_P if top_p is None else top_p
    max_iters = max_iterations or config.AGENT_MAX_ITERATIONS
    max_verify_fails = config.AGENT_MAX_VERIFY_FAILURES

    if client is None:
        client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=ipv4_httpx_client()),
        )

    notebook = EvidenceNotebook(
        max_entries=config.NOTEBOOK_MAX_ENTRIES,
        excerpt_chars=config.NOTEBOOK_EXCERPT_CHARS,
    )
    tools, state = make_researcher_tools(rag, notebook, inject_failure=inject_failure)
    tool_map = {fn.__name__: fn for fn in tools}
    ledger = TokenLedger()
    trace: list[AgentTraceStep] = []

    system = RESEARCHER_SYSTEM.format(skill_catalog=state["skill_catalog"])
    contents: list = [
        types.Content(role="user", parts=[types.Part.from_text(text=message)]),
    ]
    cfg = _usage_config(tools, temp, top_p_v, system)

    verify_failures = 0
    verify_passes = 0
    stopped_reason = "max_iterations"
    final_answer = ""
    sources: list[str] = []
    escalate = False
    clarification: str | None = None
    iterations_used = 0

    for iteration in range(1, max_iters + 1):
        iterations_used = iteration
        state["proposed"] = None
        state["clarification"] = None

        response = generate_with_retry(
            client,
            model=config.GEMINI_MODEL,
            contents=contents,
            config=cfg,
        )
        ledger.record(response, agent="researcher")

        calls = _extract_function_calls(response)
        model_content = response.candidates[0].content
        contents.append(model_content)

        if not calls:
            # Model replied in prose without a tool — nudge once via context.
            text = (response.text or "").strip()
            trace.append(
                AgentTraceStep(iteration, "researcher", "text_only", text[:200])
            )
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "You must call a tool: search_course_materials, "
                                "list_available_weeks, load_skill, ask_clarification, "
                                "or propose_answer. Do not answer in free text."
                            )
                        )
                    ],
                )
            )
            continue

        fn_response_parts = []
        for fc in calls:
            name = fc.name
            args = dict(fc.args or {})
            result_text = _run_tool(name, args, tool_map)
            trace.append(
                AgentTraceStep(
                    iteration,
                    "researcher",
                    name,
                    str(args)[:180],
                )
            )
            # Context engineering: tool result already capped/cleared by notebook.
            part_kwargs = {"name": name, "response": {"result": result_text}}
            if getattr(fc, "id", None):
                part_kwargs["id"] = fc.id
            fn_response_parts.append(types.Part.from_function_response(**part_kwargs))

        contents.append(types.Content(role="user", parts=fn_response_parts))

        if state["clarification"]:
            clarification = state["clarification"]
            final_answer = clarification
            escalate = False
            sources = notebook.sources()
            stopped_reason = "ask_clarification"
            trace.append(
                AgentTraceStep(iteration, "researcher", "stop", "ask_clarification")
            )
            break

        if state["proposed"]:
            proposal = state["proposed"]
            if single_agent:
                # Baseline: trust researcher without verifier (token comparison).
                final_answer = proposal["answer"]
                sources = proposal["sources"] or notebook.sources()
                escalate = proposal["escalate_to_human"]
                stopped_reason = "propose_single_agent"
                trace.append(
                    AgentTraceStep(iteration, "researcher", "stop", "single_agent_accept")
                )
                break

            verdict = run_verifier(
                client,
                question=message,
                proposed_answer=proposal["answer"],
                escalate=proposal["escalate_to_human"],
                evidence_digest=notebook.verifier_packet(),
                ledger=ledger,
            )
            if verdict.passed:
                verify_passes += 1
                final_answer = proposal["answer"]
                sources = proposal["sources"] or notebook.sources()
                escalate = proposal["escalate_to_human"]
                stopped_reason = "verified"
                trace.append(
                    AgentTraceStep(iteration, "verifier", "pass", verdict.issues[:200])
                )
                break

            verify_failures += 1
            trace.append(
                AgentTraceStep(iteration, "verifier", "fail", verdict.issues[:200])
            )
            state["proposed"] = None
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "Verifier FAILED grounding check:\n"
                                f"{verdict.issues}\n"
                                "Search again or revise, then propose_answer. "
                                "Do not repeat unsupported claims.\n"
                                f"{notebook.digest()}"
                            )
                        )
                    ],
                )
            )
            if verify_failures >= max_verify_fails:
                final_answer = (
                    "I could not produce a well-grounded answer from the course "
                    "materials after verification retries. Please rephrase or ask "
                    "a human mentor."
                )
                sources = notebook.sources()
                escalate = True
                stopped_reason = "max_verify_failures"
                break

    else:
        # for-else: exhausted iterations without break
        final_answer = (
            "I hit the iteration limit before finishing. Partial evidence:\n"
            + notebook.digest()
            + "\nPlease narrow the question or try again."
        )
        sources = notebook.sources()
        escalate = True
        stopped_reason = "max_iterations"

    return AgentResult(
        answer=final_answer,
        sources=sources,
        escalate_to_human=escalate,
        iterations=iterations_used,
        stopped_reason=stopped_reason,
        clarification=clarification,
        tokens=ledger.as_dict(),
        tool_log=list(state["tool_log"]),
        trace=trace,
        verification_passes=verify_passes,
        verification_failures=verify_failures,
        mode="single_agent" if single_agent else "multi_agent",
    )
