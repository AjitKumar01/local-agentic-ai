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
    is_revision = bool(state.get("review") or state.get("execution_error"))
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

    # If this is a revision pass, include feedback
    review = state.get("review")
    if review and not state.get("review_approved", False):
        parts.append("\n\n## Reviewer Feedback (MUST address all issues)\n\n")
        parts.append(review)

    exec_error = state.get("execution_error")
    if exec_error:
        parts.append("\n\n## Runtime Error (MUST fix)\n\n")
        parts.append(f"```\n{exec_error}\n```")

    previous_code = state.get("code")
    if previous_code and (review or exec_error):
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
