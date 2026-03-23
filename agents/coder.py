"""Coder agent – generates Python code from the analysis and plan."""

import logging
import re
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "coder.md"


def _extract_python_code(text: str) -> str:
    """Extract code from a ```python ... ``` block, or return the raw text."""
    match = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: try generic code fence
    match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def coder(state: AgentState, llm) -> dict:
    """Generate (or revise) Python code implementing the mathematical theory."""
    has_review = state.get("review") and not state.get("review_approved", False)
    has_exec_error = bool(state.get("execution_error"))
    is_revision = has_review or has_exec_error

    if is_revision:
        log.info("[Coder] Revising code (attempt #%d) …", state.get("revision_count", 0) + 1)
    else:
        log.info("[Coder] Generating initial code …")
    system_prompt = _PROMPT_PATH.read_text()

    # Build the user message with all available context
    parts = [
        "## Mathematical Analysis\n\n",
        state["analysis"],
        "\n\n## Implementation Plan\n\n",
        state["plan"],
    ]

    # ── Revision context: keep it focused ────────────────────────────────
    # Priority: execution errors first (concrete), then review feedback
    if has_exec_error:
        parts.append("\n\n## RUNTIME ERROR — FIX THIS FIRST\n\n")
        parts.append(f"The code below was executed and crashed with this error:\n```\n{state['execution_error']}\n```\n")
        parts.append("Fix this specific error. Do NOT rewrite the code from scratch — make the minimal change to fix the crash.\n")

    if has_review and not has_exec_error:
        # Only show review feedback if there's no exec error (exec error takes priority)
        parts.append("\n\n## Reviewer Feedback — Address ALL Issues Below\n\n")
        parts.append(state["review"])
        parts.append("\n\nFix each numbered issue. Do NOT introduce unrelated changes.\n")

    previous_code = state.get("code")
    if previous_code and is_revision:
        parts.append("\n\n## Previous Code (revise this)\n\n")
        parts.append(f"```python\n{previous_code}\n```")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="".join(parts)),
    ]

    log.info("[Coder] Calling LLM …")
    response = llm.invoke(messages)
    code = _extract_python_code(response.content)
    log.info("[Coder] Code generated (%d lines)", code.count("\n") + 1)

    return {"code": code}
