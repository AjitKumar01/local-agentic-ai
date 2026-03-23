#!/usr/bin/env python3
"""
Gradio Web UI for the Math Theory → Code pipeline.

Launch:
    python app.py                     # default: http://127.0.0.1:7860
    python app.py --port 8080         # custom port
"""

import argparse
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import gradio as gr

from graph import build_graph

# ── Config ───────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _slugify(text: str, max_len: int = 40) -> str:
    """Turn arbitrary text into a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug[:max_len]


def _save_output(theory: str, state: dict) -> Path:
    """Persist the generated code to outputs/ and return the path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(theory)
    filename = f"{ts}_{slug}.py"
    path = OUTPUT_DIR / filename
    path.write_text(state.get("code", "# No code generated"))
    return path


# ── Pipeline runner (yields incremental updates for streaming) ───────────────

def run_pipeline(theory: str, base_url: str, temperature: float):
    """Run the full agent pipeline, yielding progress updates for the UI."""
    if not theory.strip():
        yield ("", "", "", "", "", "", "⚠️ Please enter a theory description.")
        return

    log.info("Starting pipeline for: %s", theory[:80])
    app = build_graph(base_url=base_url, temperature=temperature)

    # Placeholders for each UI output
    analysis = ""
    plan = ""
    code = ""
    review = ""
    execution = ""
    saved_path = ""
    status_log = ""

    def _status(msg):
        nonlocal status_log
        ts = datetime.now().strftime("%H:%M:%S")
        status_log += f"[{ts}]  {msg}\n"

    _status("▶ Pipeline started")

    final_state = {}
    try:
        for step_output in app.stream(
            {"theory_input": theory, "revision_count": 0, "review_round": 0, "exec_round": 0},
            {"recursion_limit": 40},
        ):
            for node_name, update in step_output.items():
                final_state.update(update)
                _status(f"✓ {node_name} completed")

                # Update the relevant output
                if node_name == "theory_analyst":
                    analysis = final_state.get("analysis", "")
                elif node_name == "planner":
                    plan = final_state.get("plan", "")
                elif node_name == "coder":
                    code = final_state.get("code", "")
                elif node_name == "reviewer":
                    verdict = "✅ APPROVED" if final_state.get("review_approved") else "❌ NEEDS REVISION"
                    review = f"**{verdict}**\n\n{final_state.get('review', '')}"
                elif node_name == "executor":
                    if final_state.get("execution_success"):
                        execution = f"✅ **Success**\n```\n{final_state.get('execution_result', '')}\n```"
                    else:
                        execution = f"❌ **Error**\n```\n{final_state.get('execution_error', '')}\n```"

                revision = final_state.get("revision_count", 0)
                if revision:
                    _status(f"  ↻ Revision loop #{revision}")

                yield (analysis, plan, code, review, execution, saved_path, status_log)

    except Exception as e:
        _status(f"❌ Pipeline error: {e}")
        yield (analysis, plan, code, review, execution, saved_path, status_log)
        return

    # Save output file
    if final_state.get("code"):
        path = _save_output(theory, final_state)
        saved_path = str(path)
        _status(f"💾 Code saved to {path.name}")

    _status("▶ Pipeline finished")
    yield (analysis, plan, code, review, execution, saved_path, status_log)


# ── Gradio UI ────────────────────────────────────────────────────────────────

def create_ui():
    with gr.Blocks(
        title="Math Theory → Code",
    ) as demo:
        gr.Markdown(
            """
            # 🧮 Math Theory → Code
            **Describe a mathematical theory** and the multi-agent pipeline will
            analyse it, plan the implementation, write Python code, review it for
            correctness, and execute it — all using your local LLM.
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                theory_input = gr.Textbox(
                    label="Mathematical Theory",
                    placeholder="e.g. Implement the Adam optimizer for gradient descent…",
                    lines=4,
                )
            with gr.Column(scale=1):
                base_url = gr.Textbox(
                    label="LM Studio URL",
                    value="http://127.0.0.1:1234/v1",
                )
                temperature = gr.Slider(
                    label="Temperature",
                    minimum=0.0, maximum=1.0,
                    value=0.2, step=0.05,
                )
                run_btn = gr.Button("🚀 Run Pipeline", variant="primary", size="lg")

        status = gr.Textbox(
            label="Pipeline Log",
            lines=6,
            interactive=False,
            elem_classes=["status-box"],
        )

        with gr.Tabs():
            with gr.Tab("📝 Analysis"):
                analysis_out = gr.Markdown(label="Theory Analysis")
            with gr.Tab("📐 Plan"):
                plan_out = gr.Markdown(label="Implementation Plan")
            with gr.Tab("💻 Code"):
                code_out = gr.Code(label="Generated Python Code", language="python")
            with gr.Tab("🔍 Review"):
                review_out = gr.Markdown(label="Code Review")
            with gr.Tab("▶️ Execution"):
                execution_out = gr.Markdown(label="Execution Result")

        saved_path = gr.Textbox(label="Saved Output File", interactive=False)

        run_btn.click(
            fn=run_pipeline,
            inputs=[theory_input, base_url, temperature],
            outputs=[analysis_out, plan_out, code_out, review_out, execution_out, saved_path, status],
        )

    return demo


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Math Theory → Code  Web UI")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", help="Create a public Gradio link")
    args = parser.parse_args()

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        theme=gr.themes.Soft(),
        css=".status-box textarea { font-family: monospace; font-size: 0.85em; }",
    )
