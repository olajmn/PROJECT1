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

PROVIDER is Ollama unless TALK_PROVIDER=openrouter is set: the hosted
model is for the public demo only (docs/05-decisions.md #70), so it is
never chosen by default.
"""

import os

import ollama

from backend.model import openrouter

MODEL = "qwen3.5:9b"

# The same model as MODEL, hosted; used only when PROVIDER is "openrouter".
OPENROUTER_MODEL = "qwen/qwen3.5-9b"

# Low and global: replies drift less. Callers do not override — one
# dial for the agent.
TEMPERATURE = 0.2

PROVIDERS = ("ollama", "openrouter")
PROVIDER = os.environ.get("TALK_PROVIDER", "").strip().lower() or "ollama"
if PROVIDER not in PROVIDERS:
    # Fails at startup: a typo must not silently fall back to another model.
    raise ValueError(f"TALK_PROVIDER must be one of {PROVIDERS}, not {PROVIDER!r}")

MODEL_IN_USE = OPENROUTER_MODEL if PROVIDER == "openrouter" else MODEL


def send_chat(messages: list[dict]) -> str:
    """Send a whole conversation (`[{role, content}]`, system first,
    then alternating user/assistant) and return the raw reply text."""
    if PROVIDER == "openrouter":
        return openrouter.chat(OPENROUTER_MODEL, messages, TEMPERATURE)
    response = ollama.chat(
        model=MODEL,
        think=False,
        options={"temperature": TEMPERATURE},
        messages=messages,
    )
    return response["message"]["content"]
