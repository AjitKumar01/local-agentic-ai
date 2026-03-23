# Math Theory → Code | LangGraph Multi-Agent Pipeline

A multi-agent system that takes a **mathematical theory** described in natural language and automatically **analyses, plans, codes, reviews, and executes** a Python implementation — all powered by local LLMs via [LM Studio](https://lmstudio.ai/).

## Architecture

```
┌────────────────┐
│  Theory Input  │
└───────┬────────┘
        ▼
┌────────────────┐
│ Theory Analyst │  Breaks the theory into structured components
└───────┬────────┘
        ▼
┌────────────────┐
│    Planner     │  Designs code architecture, picks libraries
└───────┬────────┘
        ▼
┌────────────────┐◄──── Reviewer feedback loop (max 3)
│     Coder      │◄──── Executor error loop (max 3)
└───────┬────────┘
        ▼
┌────────────────┐
│   Reviewer     │  Validates math correctness & code quality
└──┬──────────┬──┘
   │ APPROVED │ NEEDS_REVISION → back to Coder
   ▼          
┌────────────────┐
│   Executor     │  Runs code in sandboxed subprocess (30s timeout)
└──┬──────────┬──┘
   │ SUCCESS  │ RUNTIME_ERROR → back to Coder
   ▼
┌────────────────┐
│  Output File   │  Saved to outputs/
└────────────────┘
```

### Agents

| Agent | Role |
|-------|------|
| **Theory Analyst** | Parses the theory into definitions, formulas, constraints, test cases |
| **Planner** | Designs function signatures, library choices, algorithmic approach |
| **Coder** | Writes a self-contained Python script (handles revision feedback) |
| **Reviewer** | Checks mathematical correctness, numerical stability, edge cases |
| **Executor** | Runs code in a sandboxed subprocess, captures output/errors |

## Prerequisites

- **Python 3.10+**
- **LM Studio** running locally with at least one model loaded
  - Default API endpoint: `http://127.0.0.1:1234/v1`
  - Uses the [OpenAI-compatible API](https://lmstudio.ai/docs/developer/openai-compat)

## Setup

```bash
# Clone / enter the project directory
cd "Local agentic AI"

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Web UI (recommended)

```bash
python app.py
```

Opens a Gradio web interface at **http://localhost:7860** where you can:
- Enter a mathematical theory in the text box
- Watch progress logs as each agent completes
- View results in separate tabs (Analysis, Plan, Code, Review, Execution)
- Generated code is auto-saved to `outputs/`

Options:
```bash
python app.py --port 8080        # custom port
python app.py --share             # create a public Gradio link
```

### CLI

```bash
# Inline theory
python main.py "Implement the Newton-Raphson method for finding roots of equations"

# Interactive prompt (press Enter twice to submit)
python main.py

# From file
python main.py --file theory.txt

# Save generated code
python main.py "Newton-Raphson method" --save output.py
```

CLI options:
```
  --base-url URL     LM Studio API base URL (default: http://127.0.0.1:1234/v1)
  -t, --temperature  LLM temperature (default: 0.2)
  -s, --save PATH    Save generated code to a file
  -f, --file PATH    Read theory from a text file
```

## Output Files

Generated code is automatically saved to the `outputs/` directory with timestamped filenames:

```
outputs/
├── 20260323_131544_newton_raphson_method.py
├── 20260323_142012_adam_optimizer_backprop.py
└── ...
```

## Project Structure

```
.
├── app.py                  # Gradio web UI
├── main.py                 # CLI entry point
├── graph.py                # LangGraph StateGraph definition and wiring
├── state.py                # AgentState TypedDict
├── requirements.txt        # Python dependencies
├── agents/
│   ├── theory_analyst.py   # Theory analysis node
│   ├── planner.py          # Code planning node
│   ├── coder.py            # Code generation node (handles revisions)
│   ├── reviewer.py         # Math/code review node
│   └── executor.py         # Sandboxed execution node
├── prompts/
│   ├── theory_analyst.md   # System prompt for analysis
│   ├── planner.md          # System prompt for planning
│   ├── coder.md            # System prompt for code generation
│   └── reviewer.md         # System prompt for review
└── outputs/                # Auto-generated code files
```

## Example

**Input:**
> Implement the Newton-Raphson method for finding roots of equations

**Pipeline:**
```
[13:13:44]  ▶ Pipeline started
[13:14:27]  ✓ theory_analyst completed
[13:15:03]  ✓ planner completed
[13:15:35]  ✓ coder completed
[13:15:57]  ✓ reviewer completed  (APPROVED)
[13:15:57]  ✓ executor completed  (Success)
[13:15:57]  💾 Code saved to 20260323_131544_newton_raphson.py
[13:15:57]  ▶ Pipeline finished
```

**Output:** A complete Python script implementing Newton-Raphson with test cases, saved to `outputs/`.

## Configuration

All agents use the same local LLM, differentiated by system prompts (see `prompts/`). To use a specific model, configure it in LM Studio before running the pipeline.

| Setting | Default | Description |
|---------|---------|-------------|
| Base URL | `http://127.0.0.1:1234/v1` | LM Studio API endpoint |
| Temperature | `0.2` | Low for deterministic code generation |
| Max revisions | `3` | Feedback loop cap (configurable in `graph.py`) |
| Execution timeout | `30s` | Subprocess timeout (configurable in `agents/executor.py`) |
