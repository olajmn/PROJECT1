"""
Talk to the local model (Ollama) and validate that what comes back has
the expected shape.

Generic on purpose: sends a system+user message in JSON mode, parses
the response, and checks that a given list of keys is present - it has
no idea what a "plan" is. The caller (planner.py) passes in which keys
to require, rather than this module reading planner.PLAN_KEYS directly
- that would import back into planner.py, a circular import.

Split out of planner.py (formerly plan.py) as its own module,
2026-08-27.

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).
"""

import json

import ollama

MODEL = "llama3.1:8b"


def ask_model(system_prompt: str, user_content: str, required_keys: tuple[str, ...]) -> dict:
    """
    Send a system prompt + user message to the local model asking for
    JSON, parse the response, and validate it has every key in
    `required_keys` - so every caller can trust the shape instead of
    re-checking it themselves.
    """
    response = ollama.chat(
        model=MODEL,
        format="json",  # ask Ollama to constrain output to valid JSON
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    plan = json.loads(response["message"]["content"])

    missing = [key for key in required_keys if key not in plan]
    if missing:
        raise ValueError(
            f"Model response is missing required plan key(s) {missing}: {plan}"
        )
    return plan
