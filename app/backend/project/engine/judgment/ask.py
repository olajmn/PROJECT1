"""Ask the model for JSON and check the boxes came back right.

Sends system + user text through llm_client, parses JSON, and makes
sure every required key is a string or null. Callers pass which keys
they need — this file does not know about plans.
"""

import json

from backend.llm_client import call_with_retry, send_message


def ask(system_prompt: str, user_content: str, required_keys: tuple[str, ...]) -> dict:
    """Ask the model; return a dict with every key in `required_keys`."""

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


# Older name — same function.
ask_model = ask
