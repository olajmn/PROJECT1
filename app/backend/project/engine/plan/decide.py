"""
Stage 3 Decide — enough to start co-building a Project map?

Thin judgment only: ASK (clarification), SUGGEST (suggested_action
or suggested_duration), or PLAN (all three null). Does not write
horizons or steps; generate_plan() calls fill only when this returns
planable. Parameter `goal` is still the stored project text
(goal_id engine) — see docs/05-decisions.md #25.
"""

from backend.foundation.time import resolve_duration
from backend.store.data_persistence import get_vision
from backend.project.engine.plan.json_request import ask_model
from backend.project.engine.plan.plan_prompts import DECIDE_SYSTEM_PROMPT
from backend.project.engine.plan.plan_schema import _now_str

DECIDE_KEYS = ("clarification", "suggested_action", "suggested_duration")


def decide(
    goal: str,
    duration: str | None = None,
    vision_id: int | None = None,
    prior_suggestion: str | None = None,
    reply: str | None = None,
    opening: bool = False,
) -> dict:
    """
    One model call: {clarification, suggested_action, suggested_duration},
    each a string or null. Callers (generate_plan) enforce mutual
    exclusion and opening rules after this returns. Opening asks for a
    clear enough End when the project is thin; missing timeframe must
    not force ASK.
    """
    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My project is: {goal}"
    )
    if vision_id is not None:
        vision = get_vision(vision_id)
        if vision is not None:
            user_content += (
                f"\n\nThis project is part of a broader direction: "
                f"{vision['text']}"
            )
    if prior_suggestion:
        user_content += (
            f"\n\nYou previously suggested this as a possible first step, "
            f"before the user replied: \"{prior_suggestion}\""
        )
        if reply:
            user_content += (
                f"\n\nThe user's reply to that suggestion: {reply}\n\n"
                "Read the reply in light of what you just suggested - it may "
                "accept it, correct or add to your understanding of the "
                "project, or propose something else of their own, rather "
                "than being an unrelated restatement of the project."
            )
    if duration:
        user_content += (
            f"\n\nI want this project to span roughly: "
            f"{resolve_duration(duration)}"
        )
    else:
        user_content += "\n\nNo timeframe was given for this project."
    if opening:
        user_content += (
            "\n\nThis is the opening of a new project. Your job is to get "
            "enough to start a coarse map with the user - not to propose a "
            "first action to do right now, and not to invent a full plan "
            "alone. Do not set suggested_action. If the project has no "
            "clear enough end (what 'far enough for now' looks like), set "
            "clarification to one short question about that. Missing "
            "timeframe is fine - do not ask about timeframe on opening, "
            "and never invent a default like '8 weeks' in "
            "suggested_duration. Prefer welcoming project language over "
            "calling the aim a 'broad goal'."
        )
    return ask_model(DECIDE_SYSTEM_PROMPT, user_content, DECIDE_KEYS)
