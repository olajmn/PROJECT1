"""
Reasoning
=========

The one boundary every call to the local model (Ollama) passes
through - send a system+user message, get the raw text response back.
Never decides anything and never interprets what the text means; that
is each caller's own job (see planning/plan/model_client.py's
ask_model() for the Plan-specific JSON interpretation built on top of
this, and planning/feedback/acknowledger.py for a plain-text one).

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull qwen3.5:9b).

MODEL below is the only place the concrete local model is named -
every caller goes through send_message() and never sees which model
is behind it, so swapping models is a one-line change here, not a
change to this module's callers or interface (see docs/05-decisions.md
for the current model choice and why it's expected to change again).

think=False is passed unconditionally, not just for the current
model - some models (e.g. qwen3.5:9b) support an extended "thinking"
mode Ollama exposes as a separate response channel; left enabled, it
was observed taking 3+ minutes and returning empty `content` under
format="json" (the internal reasoning trace consumed the response
without ever producing the constrained JSON output this project's
callers require - see docs/05-decisions.md #21). Harmless no-op for a
model with no such capability (llama3.1:8b included) - Ollama simply
ignores it - so this stays correct regardless of which model is
behind MODEL, rather than being a qwen-specific branch.
"""

import ollama

MODEL = "qwen3.5:9b"


def send_message(system_prompt: str, user_content: str, json_mode: bool = False) -> str:
    """
    Send a system prompt + user message to the local model, return the
    raw text response. `json_mode=True` asks Ollama to constrain its
    output to valid JSON syntax - still just text here; parsing and
    validating the shape of that JSON is the caller's job, not this
    function's.
    """
    response = ollama.chat(
        model=MODEL,
        format="json" if json_mode else None,
        think=False,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response["message"]["content"]


def call_with_retry(attempt, attempts: int = 3):
    """
    Calls the zero-argument `attempt()` up to `attempts` times,
    returning the first result that doesn't raise. `attempt` is
    expected to be a caller's own "send_message() + parse + validate
    shape" sequence, raising ValueError (json.JSONDecodeError is a
    ValueError subclass, so a malformed JSON body is covered too) on a
    bad shape - see planning/plan/model_client.py's ask_model() and
    planning/plan/plan_structure.py's generate_structure() for the two
    current callers.

    Exists because this project has repeatedly observed the local
    model occasionally not follow the requested JSON shape exactly (a
    missing key, a string field returned as a nested object) and then
    produce a correctly-shaped response on a bare retry with no code
    change - see docs/04-current-state.md § 4. A bounded retry is
    cheap insurance against that observed pattern, not a fix for a
    deeper problem, and not a guarantee - the last attempt's exception
    is re-raised unchanged if every attempt fails, so a genuine,
    persistent failure still surfaces as one, just a rarer one.
    """
    last_error: ValueError | None = None
    for _ in range(attempts):
        try:
            return attempt()
        except ValueError as e:
            last_error = e
    raise last_error
