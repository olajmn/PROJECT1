"""
Construct a shallow WHAT progression (shadow).

This is the structural axis from docs/planning-model.md: ordered Steps
for what must happen toward the Goal. It deliberately does NOT use
week_windows / day_windows — calendar length must not dictate how many
progression steps exist.

First mint stays coarse on purpose: a few phase-level claims only.
Lesson-level detail belongs under edit_map / call_suggest,
not this call — otherwise the agent finishes the middle without the user.

Written onto plan["progression"] by generate_plan() after Decide=PLAN.
Active prefers this field via manifestation.to_planning_node() when
present; legacy plan["steps"] remains a fallback. Not yet the sole
source of truth — calendar fill and PLAN_KEYS still run beside it.
"""

import json

from backend.llm_client import call_with_retry, send_message
from backend.project.panes.canvas.bead import Step, from_nested_labels

# Hard cap: first glance must stay note-sized. Zoom adds depth later.
_MIN_STEPS = 2
_MAX_STEPS = 4

PROGRESSION_SYSTEM_PROMPT = (
    "You list what must happen for the user's goal to be fulfilled — "
    "the progression of work, not a calendar schedule. "
    "Do NOT invent one step per week or per day. "
    "Do NOT name months, weekdays, or dates as the structure. "
    "This is the FIRST, coarse outline only — co-built with the user "
    "later. Each step MUST be a phase name of at most 5 words "
    "(examples: 'Basics', 'Set up tools', 'Build one page', "
    "'Make it interactive'). Forbidden: full sentences, lesson "
    "descriptions, HTML/CSS/JS as separate curriculum steps, tool "
    "lists, or anything that already teaches how. Detail comes later "
    "when the user expands a phase. "
    "Respond with ONLY a JSON object with exactly one key, \"steps\", "
    "whose value is an array of 2 to 4 short phase labels, in the "
    "order they should happen. Prefer fewer. "
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
            label = item.strip()
            # Soft truncate runaway syllabus sentences the model still emits.
            words = label.split()
            if len(words) > 5:
                label = " ".join(words[:5])
            labels.append(label)
        if len(labels) < _MIN_STEPS or len(labels) > _MAX_STEPS:
            raise ValueError(
                f"Progression needs {_MIN_STEPS}–{_MAX_STEPS} steps, "
                f"got {len(labels)}: {data}"
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
