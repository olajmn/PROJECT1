"""
Plan-specific interpretation of a model response: sends a system+user
message through the shared Reasoning boundary
(reasoning.model_client.send_message()), then parses and validates
that the result has the expected plan shape. Generic on purpose beyond
that: this only knows how to check that a given list of keys is
present in the parsed JSON - it has no idea what a "plan" is. The
caller (planner.py) passes in which keys to require, rather than this
module reading planner.PLAN_KEYS directly - that would import back
into planner.py, a circular import.

Split out of planner.py (formerly plan.py) as its own module,
2026-08-27; the raw model call moved again, the same day, into
reasoning.model_client once goals/feedback/acknowledger.py became a
second, independent caller of it.
"""

import json

from backend.reasoning.model_client import send_message


def ask_model(system_prompt: str, user_content: str, required_keys: tuple[str, ...]) -> dict:
    """
    Send a system prompt + user message to the local model asking for
    JSON, parse the response, and validate it has every key in
    `required_keys` - so every caller can trust the shape instead of
    re-checking it themselves.
    """
    raw = send_message(system_prompt, user_content, json_mode=True)
    plan = json.loads(raw)

    missing = [key for key in required_keys if key not in plan]
    if missing:
        raise ValueError(
            f"Model response is missing required plan key(s) {missing}: {plan}"
        )
    return plan
