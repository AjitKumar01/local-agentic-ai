"""Quick smoke-test for each agent."""
import logging, sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")

# ── 1. Executor test (no LLM needed) ────────────────────────────────────
from agents.executor import executor

code = 'import math\nprint(f"sqrt(2) = {math.sqrt(2):.10f}")\nprint("Done!")'
result = executor({"code": code})
assert result["execution_success"], f"Executor failed: {result['execution_error']}"
print(f"[TEST] Executor OK: {result['execution_result'].strip()}")

# ── 2. Reviewer test ────────────────────────────────────────────────────
from langchain_openai import ChatOpenAI
from agents.reviewer import reviewer

llm = ChatOpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio", temperature=0.2)

state = {
    "analysis": "Newton-Raphson root finding. Formula: x_{n+1} = x_n - f(x_n)/f'(x_n).",
    "plan": "One function: newton_raphson(f, fprime, x0, tol, max_iter) -> root.",
    "code": '''import numpy as np

def newton_raphson(f, fprime, x0, tol=1e-10, max_iter=100):
    x = x0
    for i in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x, i
        fpx = fprime(x)
        if fpx == 0:
            raise ValueError("Zero derivative")
        x = x - fx / fpx
    raise RuntimeError("Did not converge")

if __name__ == "__main__":
    root, iters = newton_raphson(lambda x: x**2 - 2, lambda x: 2*x, 1.0)
    print(f"Root: {root:.10f}, Iterations: {iters}")
''',
}
result = reviewer(state, llm)
print(f"[TEST] Reviewer OK: approved={result['review_approved']}")

print("\n[TEST] All agents passed!")
