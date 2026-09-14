"""
A JSON request to the model: sends a system+user message through the
shared model boundary (model.client.send_message()), then parses the
response and validates that a given list of keys is present, each
holding a string or null. Not a second model client, and not
plan-aware despite living under plan/ - it has no idea what a "plan"
is. The caller (planner.py) passes in which keys to require, rather
than this module reading planner.PLAN_KEYS directly - that would
import back into planner.py, a circular import.

Split out of planner.py (formerly plan.py) as its own module,
2026-08-27; the raw model call moved again, the same day, into the
shared model boundary once planning/feedback/acknowledger.py became a
second, independent caller of it. Named model_client.py until
2026-09-14, when it collided with the actual model client.
"""

import json

from backend.model.client import call_with_retry, send_message


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

        missing = [key for key in required_keys if key not in plan]
        if missing:
            raise ValueError(
                f"Model response is missing required plan key(s) {missing}: {plan}"
            )
        wrong_type = [
            key for key in required_keys
            if key in plan and not isinstance(plan[key], (str, type(None)))
        ]
        if wrong_type:
            raise ValueError(
                f"Model response has non-string value(s) for plan key(s) {wrong_type}: {plan}"
            )
        return plan

    return call_with_retry(attempt)
