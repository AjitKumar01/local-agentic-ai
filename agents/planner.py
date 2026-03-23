"""Planner agent – designs the code architecture for a mathematical implementation."""

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "planner.md"


def planner(state: AgentState, llm) -> dict:
    """Produce an implementation plan from the structured analysis."""
    log.info("[Planner] Designing implementation plan …")
    system_prompt = _PROMPT_PATH.read_text()

    user_msg = (
        "## Mathematical Analysis\n\n"
        f"{state['analysis']}\n"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg),
    ]

    log.info("[Planner] Calling LLM …")
    response = llm.invoke(messages)
    log.info("[Planner] Plan complete (%d chars)", len(response.content))

    return {"plan": response.content}
