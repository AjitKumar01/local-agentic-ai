"""Reviewer agent – validates generated code for mathematical correctness."""

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "reviewer.md"


def reviewer(state: AgentState, llm) -> dict:
    """Review code against the analysis and plan; return verdict + feedback."""
    review_round = state.get("review_round", 0)
    log.info("[Reviewer] Reviewing generated code (round %d) …", review_round + 1)
    system_prompt = _PROMPT_PATH.read_text()

    parts = [
        "## Mathematical Analysis\n\n",
        state["analysis"],
        "\n\n## Implementation Plan\n\n",
        state["plan"],
        "\n\n## Generated Code\n\n",
        f"```python\n{state['code']}\n```",
    ]

    # If this is a re-review, tell the reviewer what was asked previously
    if review_round > 0 and state.get("review"):
        parts.append("\n\n## Previous Review (round " + str(review_round) + ")\n\n")
        parts.append(state["review"])
        parts.append(
            "\n\n**IMPORTANT**: This is revision round " + str(review_round + 1) + ". "
            "Check ONLY whether the issues from the previous review were fixed. "
            "If they were fixed, APPROVE. Do NOT raise new minor issues.\n"
        )

    user_msg = "".join(parts)

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
