"""LangGraph state-graph definition and wiring for the math-theory-to-code pipeline."""

from functools import partial

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.coder import coder
from agents.executor import executor
from agents.planner import planner
from agents.reviewer import reviewer
from agents.theory_analyst import theory_analyst
from state import AgentState

MAX_REVISIONS = 3


def _get_llm(base_url: str = "http://127.0.0.1:1234/v1", temperature: float = 0.2) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at the local LM Studio server."""
    return ChatOpenAI(
        base_url=base_url,
        api_key="lm-studio",
        temperature=temperature,
    )


# ── Routing helpers ──────────────────────────────────────────────────────────

def _after_reviewer(state: AgentState) -> str:
    """Decide where to go after the reviewer node."""
    if state.get("review_approved"):
        return "executor"
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return END
    return "coder"


def _after_executor(state: AgentState) -> str:
    """Decide where to go after the executor node."""
    if state.get("execution_success"):
        return END
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return END
    return "coder"


# ── Node wrappers (inject LLM + bump revision counter) ──────────────────────

def _make_theory_analyst_node(llm):
    def _node(state: AgentState) -> dict:
        return theory_analyst(state, llm)
    return _node


def _make_planner_node(llm):
    def _node(state: AgentState) -> dict:
        return planner(state, llm)
    return _node


def _make_coder_node(llm):
    def _node(state: AgentState) -> dict:
        result = coder(state, llm)
        # Bump revision count whenever the coder runs after the first time
        revision_count = state.get("revision_count", 0)
        if state.get("review") or state.get("execution_error"):
            revision_count += 1
        result["revision_count"] = revision_count
        return result
    return _node


def _make_reviewer_node(llm):
    def _node(state: AgentState) -> dict:
        return reviewer(state, llm)
    return _node


def _executor_node(state: AgentState) -> dict:
    return executor(state)


# ── Graph builder ────────────────────────────────────────────────────────────

def build_graph(base_url: str = "http://127.0.0.1:1234/v1", temperature: float = 0.2):
    """Construct and compile the LangGraph state graph."""
    llm = _get_llm(base_url=base_url, temperature=temperature)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("theory_analyst", _make_theory_analyst_node(llm))
    graph.add_node("planner", _make_planner_node(llm))
    graph.add_node("coder", _make_coder_node(llm))
    graph.add_node("reviewer", _make_reviewer_node(llm))
    graph.add_node("executor", _executor_node)

    # Linear edges
    graph.set_entry_point("theory_analyst")
    graph.add_edge("theory_analyst", "planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "reviewer")

    # Conditional edges
    graph.add_conditional_edges("reviewer", _after_reviewer, {
        "executor": "executor",
        "coder": "coder",
        END: END,
    })
    graph.add_conditional_edges("executor", _after_executor, {
        END: END,
        "coder": "coder",
    })

    return graph.compile()
