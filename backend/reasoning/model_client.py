"""
Reasoning
=========

The one boundary every call to the local model (Ollama) passes
through - send a system+user message, get the raw text response back.
Never decides anything and never interprets what the text means; that
is each caller's own job (see goals/plan/model_client.py's
ask_model() for the Plan-specific JSON interpretation built on top of
this, and goals/feedback/acknowledger.py for a plain-text one).

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).
"""

import ollama

MODEL = "llama3.1:8b"


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
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response["message"]["content"]
