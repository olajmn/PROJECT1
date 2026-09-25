"""
The one boundary every local-model call passes through: system + user
(or a whole chat) in, raw text out. Callers interpret that text (JSON shape, meaning);
this module does not.

MODEL is the only place the concrete model is named, so a swap is a
one-line change here (see docs/05-decisions.md). TEMPERATURE is likewise
set once here for every call — not per call site.

think=False is unconditional, not a qwen-specific branch. Some
models expose a separate thinking channel; left on, it has taken 3+
minutes and returned empty `content` under format="json" because the
trace consumed the response (docs/05-decisions.md #21). Models
without that channel ignore the flag.
"""

import ollama

MODEL = "qwen3.5:9b"

# Low and global: structured JSON (Suggest, Read map) and chat
# both drift less. Callers do not override — one dial for the agent.
TEMPERATURE = 0.2


def send_message(
    system_prompt: str,
    user_content: str,
    json_mode: bool = False,
    schema: dict | None = None,
) -> str:
    """Send system + user to the local model; return raw text.

    json_mode asks Ollama for JSON *syntax* only - the caller still
    has to parse and validate the shape. A `schema` (a JSON Schema
    dict) instead constrains generation itself, so a response that
    doesn't fit the shape cannot come back at all; it takes precedence
    when both are given.
    """
    response = ollama.chat(
        model=MODEL,
        format=schema if schema is not None else ("json" if json_mode else None),
        think=False,
        options={"temperature": TEMPERATURE},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response["message"]["content"]


def send_chat(messages: list[dict]) -> str:
    """Send a whole conversation (`[{role, content}]`, system first,
    then alternating user/assistant) and return the raw reply text.

    Plain chat: no JSON format. Same model, temperature, and think
    setting as send_message()."""
    response = ollama.chat(
        model=MODEL,
        think=False,
        options={"temperature": TEMPERATURE},
        messages=messages,
    )
    return response["message"]["content"]


def call_with_retry(attempt, attempts: int = 3):
    """Call zero-arg `attempt()` up to `attempts` times; return the
    first success.

    `attempt` should send, parse, and validate, raising ValueError on
    a bad shape (JSONDecodeError is a ValueError). The local model
    sometimes returns a malformed body and a correctly-shaped one on
    an unchanged retry (docs/04-current-state.md § 4) - this is
    bounded insurance, not a guarantee. Persistent failure still
    re-raises the last error.
    """
    last_error: ValueError | None = None
    for _ in range(attempts):
        try:
            return attempt()
        except ValueError as e:
            last_error = e
    raise last_error
