"""
A JSON request to the model: sends a system+user message through the
shared model boundary (backend.llm_client.send_message()), then parses the
response and validates that a given list of keys is present, each
holding a string or null. Not a second model client, and not
plan-aware despite living under plan/ - it has no idea what a "plan"
is. The caller (planner.py) passes in which keys to require, rather
than this module reading planner.PLAN_KEYS directly - that would
import back into planner.py, a circular import.

Split out of planner.py (formerly plan.py) as its own module,
2026-08-27; the raw model call moved again, the same day, into the
shared LLM boundary once project/panes/chat/feedback/acknowledger.py became a
second, independent caller of it. This file was briefly named
model_client.py until 2026-09-14 (collided with the real client);
the shared boundary is now backend/llm_client.py.
"""

import json

from backend.llm_client import call_with_retry, send_message


def ask_model(system_prompt: str, user_content: str, required_keys: tuple[str, ...]) -> dict:
    """
    Send a system prompt + user message to the local model asking for
    JSON, parse the response, and validate it has every key in
    `required_keys`, each holding a string or JSON null - so every
    caller can trust both the shape and the value types instead of
    re-checking them themselves. Retried a few times on a bad shape
    (see model.client.call_with_retry's own docstring for
    why) before finally raising.
    """

    def attempt() -> dict:
        raw = send_message(system_prompt, user_content, json_mode=True)
        plan = json.loads(raw)
        if not isinstance(plan, dict):
            raise ValueError(f"Model response is not a JSON object: {plan!r}")

        # Local models often omit broad horizons (year/month) when the
        # span is short. Treat missing keys as null rather than failing
        # the whole Fill/replan — callers already accept null values.
        for key in required_keys:
            if key not in plan:
                plan[key] = None

        wrong_type = [
            key for key in required_keys
            if not isinstance(plan[key], (str, type(None)))
        ]
        if wrong_type:
            raise ValueError(
                f"Model response has non-string value(s) for plan key(s) {wrong_type}: {plan}"
            )
        return plan

    return call_with_retry(attempt)
