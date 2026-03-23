"""Theory Analyst agent – breaks a mathematical theory into structured components."""

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "theory_analyst.md"


def theory_analyst(state: AgentState, llm) -> dict:
    """Analyse the raw theory input and return a structured breakdown."""
    log.info("[Theory Analyst] Starting analysis of input theory …")
    system_prompt = _PROMPT_PATH.read_text()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["theory_input"]),
    ]

    log.info("[Theory Analyst] Calling LLM …")
    response = llm.invoke(messages)
    log.info("[Theory Analyst] Analysis complete (%d chars)", len(response.content))

    return {"analysis": response.content}
