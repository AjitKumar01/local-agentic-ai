#!/usr/bin/env python3
"""
Math Theory → Code  |  LangGraph Multi-Agent Pipeline

Accepts a mathematical theory description and produces a verified Python
implementation using a chain of specialised agents:

  Theory Analyst → Planner → Coder ⇄ Reviewer → Executor

Usage:
    python main.py                          # interactive prompt
    python main.py "Newton-Raphson method"  # pass theory directly
    python main.py --file theory.txt        # read from file
"""

import argparse
import logging
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

from graph import build_graph

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def _print_section(title: str, body: str) -> None:
    width = 72
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")
    print(body)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate & execute Python code for a mathematical theory."
    )
    parser.add_argument("theory", nargs="?", help="Theory description (inline).")
    parser.add_argument("--file", "-f", help="Read theory from a text file.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:1234/v1",
        help="LM Studio API base URL (default: http://127.0.0.1:1234/v1)",
    )
    parser.add_argument(
        "--temperature", "-t", type=float, default=0.2, help="LLM temperature."
    )
    parser.add_argument(
        "--save", "-s", help="Save generated code to this file path."
    )
    args = parser.parse_args()

    # ── Logging setup ────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve theory input
    if args.file:
        with open(args.file) as fh:
            theory_input = fh.read().strip()
    elif args.theory:
        theory_input = args.theory
    else:
        print("Enter the mathematical theory (press Enter twice to submit):\n")
        lines: list[str] = []
        try:
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        theory_input = "\n".join(lines).strip()

    if not theory_input:
        print("Error: No theory provided.", file=sys.stderr)
        sys.exit(1)

    print(f"\n▶ Theory: {theory_input[:120]}{'…' if len(theory_input) > 120 else ''}")
    print("▶ Building agent graph …")

    app = build_graph(base_url=args.base_url, temperature=args.temperature)

    print("▶ Running pipeline …\n")

    # Stream the graph so we can show progress
    final_state = None
    for step_output in app.stream(
        {"theory_input": theory_input, "revision_count": 0, "review_round": 0, "exec_round": 0},
        {"recursion_limit": 40},
    ):
        # step_output is {node_name: state_update}
        for node_name, update in step_output.items():
            print(f"  ✓ {node_name} completed")
            final_state = {**(final_state or {}), **update}

    if final_state is None:
        print("Error: pipeline produced no output.", file=sys.stderr)
        sys.exit(1)

    # ── Display results ──────────────────────────────────────────────────
    _print_section("ANALYSIS", final_state.get("analysis", "(none)"))
    _print_section("PLAN", final_state.get("plan", "(none)"))
    _print_section("GENERATED CODE", final_state.get("code", "(none)"))
    _print_section("REVIEW", final_state.get("review", "(none)"))

    if final_state.get("execution_success"):
        _print_section("EXECUTION OUTPUT ✅", final_state.get("execution_result", ""))
    elif final_state.get("execution_error"):
        _print_section("EXECUTION ERROR ❌", final_state.get("execution_error", ""))
    else:
        _print_section(
            "STATUS",
            "Code was not executed (max revisions reached before approval).",
        )

    revisions = final_state.get("revision_count", 0)
    if revisions:
        print(f"\n  ↻ Revision loops: {revisions}")

    # ── Auto-save to outputs/ ────────────────────────────────────────────
    if final_state.get("code"):
        OUTPUT_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", theory_input[:40]).strip("_").lower()
        auto_path = OUTPUT_DIR / f"{ts}_{slug}.py"
        auto_path.write_text(final_state["code"])
        print(f"\n  💾 Code auto-saved to {auto_path}")

    # ── Optionally save to custom path ───────────────────────────────────
    if args.save and final_state.get("code"):
        with open(args.save, "w") as f:
            f.write(final_state["code"])
        print(f"  💾 Code also saved to {args.save}")

    print()


if __name__ == "__main__":
    main()
