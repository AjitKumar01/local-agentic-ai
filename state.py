"""Shared state schema for the LangGraph math-theory-to-code pipeline."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State passed between nodes in the graph."""

    # Input
    theory_input: str

    # Theory Analyst output
    analysis: str

    # Planner output
    plan: str

    # Coder output
    code: str

    # Reviewer output
    review: str
    review_approved: bool

    # Executor output
    execution_result: str
    execution_error: str
    execution_success: bool

    # Loop control
    revision_count: int
