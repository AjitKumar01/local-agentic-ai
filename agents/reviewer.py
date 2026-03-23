"""Reviewer agent – validates generated code for mathematical correctness."""

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "reviewer.md"


def reviewer(state: AgentState, llm) -> dict:
    """Review code against the analysis and plan; return verdict + feedback."""
    log.info("[Reviewer] Reviewing generated code …")
    system_prompt = _PROMPT_PATH.read_text()

    user_msg = (
        "## Mathematical Analysis\n\n"
        f"{state['analysis']}\n\n"
        "## Implementation Plan\n\n"
        f"{state['plan']}\n\n"
        "## Generated Code\n\n"
        f"```python\n{state['code']}\n```"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg),
    ]

    log.info("[Reviewer] Calling LLM …")
    response = llm.invoke(messages)
    content = response.content

    approved = "VERDICT: APPROVED" in content
    log.info("[Reviewer] Verdict: %s", "APPROVED" if approved else "NEEDS_REVISION")

    return {
        "review": content,
        "review_approved": approved,
    }
