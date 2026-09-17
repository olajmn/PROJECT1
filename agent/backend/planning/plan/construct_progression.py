"""
Construct a shallow WHAT progression (shadow).

This is the structural axis from docs/planning-model.md: ordered Steps
for what must happen toward the Goal. It deliberately does NOT use
week_windows / day_windows — calendar length must not dictate how many
progression steps exist.

Written onto plan["progression"] by generate_plan() after Decide=PLAN.
Active prefers this field via manifestation.to_planning_node() when
present; legacy plan["steps"] remains a fallback. Not yet the sole
source of truth — calendar fill and PLAN_KEYS still run beside it.
"""

import json

from backend.model.client import call_with_retry, send_message
from backend.planning.plan.step import Step, from_nested_labels

PROGRESSION_SYSTEM_PROMPT = (
    "You list what must happen for the user's goal to be fulfilled — "
    "the progression of work, not a calendar schedule. "
    "Do NOT invent one step per week or per day. "
    "Do NOT name months, weekdays, or dates as the structure. "
    "Each step is a short claim about something that needs to become "
    "true or get done. "
    "Respond with ONLY a JSON object with exactly one key, \"steps\", "
    "whose value is an array of 2 to 8 short strings, in the order "
    "they should happen. "
    "If you are given an immediate action, the first step should lead "
    "into or match that action."
)


def construct_progression(
    goal: str,
    right_now: str | None = None,
    duration: str | None = None,
) -> dict | None:
    """
    {"steps": [Step.to_dict(), ...]} or None if the model returns
    nothing usable. Duration, when present, is context only ("the user
    hopes this fits in roughly X") — never a step count.
    """
    user_content = f"My goal is: {goal}"
    if right_now:
        user_content += f"\n\nThe immediate action already decided is: {right_now}"
    if duration:
        user_content += (
            f"\n\nThe user hopes this fits in roughly: {duration}. "
            "Use that only as background; do not turn it into one step "
            "per time unit."
        )

    def attempt() -> list[str]:
        raw = send_message(PROGRESSION_SYSTEM_PROMPT, user_content, json_mode=True)
        data = json.loads(raw)
        steps = data.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"Progression response missing steps list: {data}")
        labels = []
        for item in steps:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Progression step is not a non-empty string: {data}")
            labels.append(item.strip())
        if len(labels) < 2 or len(labels) > 8:
            raise ValueError(
                f"Progression needs 2–8 steps, got {len(labels)}: {data}"
            )
        return labels

    try:
        labels = call_with_retry(attempt)
    except (ValueError, json.JSONDecodeError, TypeError):
        # Shadow must not break minting — legacy plan.steps / now still work.
        return None

    counter = {"n": 0}

    def mint_id() -> str:
        counter["n"] += 1
        return f"p{counter['n']}"

    entries = [{"label": label, "children": []} for label in labels]
    steps = from_nested_labels(entries, mint_id)
    return {"steps": [step.to_dict() for step in steps]}


def progression_from_dicts(data: dict | None) -> list[Step]:
    """Load shadow progression steps from a saved plan field."""
    if not data or not isinstance(data, dict):
        return []
    raw = data.get("steps")
    if not isinstance(raw, list):
        return []
    return [Step.from_dict(item) for item in raw if isinstance(item, dict)]
