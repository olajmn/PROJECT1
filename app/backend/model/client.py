"""
The one boundary every local-model call passes through: a whole chat in,
raw text out. Callers interpret that text; this module does not.

MODEL is the only place the concrete model is named, so a swap is a
one-line change here (see docs/05-decisions.md). TEMPERATURE is likewise
set once here for every call — not per call site.

think=False is unconditional, not a qwen-specific branch. Some
models expose a separate thinking channel; left on, it has taken 3+
minutes and returned empty `content` because the trace consumed the
response (docs/05-decisions.md #21). Models without that channel
ignore the flag.
"""

import ollama

MODEL = "qwen3.5:9b"

# Low and global: replies drift less. Callers do not override — one
# dial for the agent.
TEMPERATURE = 0.2


def send_chat(messages: list[dict]) -> str:
    """Send a whole conversation (`[{role, content}]`, system first,
    then alternating user/assistant) and return the raw reply text."""
    response = ollama.chat(
        model=MODEL,
        think=False,
        options={"temperature": TEMPERATURE},
        messages=messages,
    )
    return response["message"]["content"]
