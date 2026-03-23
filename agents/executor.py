"""Executor agent – runs generated Python code in a sandboxed subprocess."""

import logging
import subprocess
import tempfile
from pathlib import Path

from state import AgentState

log = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 30


def executor(state: AgentState, **_kwargs) -> dict:
    """Write code to a temp file, execute it, and capture output."""
    log.info("[Executor] Running generated code …")
    code = state["code"]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )

        if result.returncode == 0:
            log.info("[Executor] Code executed successfully (exit 0)")
            return {
                "execution_result": result.stdout,
                "execution_error": "",
                "execution_success": True,
            }
        else:
            log.warning("[Executor] Code failed (exit %d): %s", result.returncode, result.stderr[:200])
            return {
                "execution_result": result.stdout,
                "execution_error": result.stderr,
                "execution_success": False,
            }

    except subprocess.TimeoutExpired:
        log.warning("[Executor] Timed out after %ds", _TIMEOUT_SECONDS)
        return {
            "execution_result": "",
            "execution_error": f"Execution timed out after {_TIMEOUT_SECONDS} seconds.",
            "execution_success": False,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)
