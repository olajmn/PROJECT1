"""
Stage 3 Decide — enough information to plan?

Thin judgment only: ASK (clarification), SUGGEST (suggested_action
or suggested_duration), or PLAN (all three null). Does not write
horizons or steps; generate_plan() calls fill only when this returns
planable.
"""

from backend.foundation.time import resolve_duration
from backend.infrastructure.data_persistence import get_vision
from backend.planning.plan.json_request import ask_model
from backend.planning.plan.plan_prompts import DECIDE_SYSTEM_PROMPT
from backend.planning.plan.plan_schema import _now_str

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
    exclusion and opening rules after this returns.
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if vision_id is not None:
        vision = get_vision(vision_id)
        if vision is not None:
            user_content += f"\n\nThis goal is part of a broader direction: {vision['text']}"
    if prior_suggestion:
        user_content += (
            f"\n\nYou previously suggested this as a possible first step, "
            f"before the user replied: \"{prior_suggestion}\""
        )
        if reply:
            user_content += (
                f"\n\nThe user's reply to that suggestion: {reply}\n\n"
                "Read the reply in light of what you just suggested - it may accept it, "
                "correct or add to your understanding of the goal, or propose something "
                "else of their own, rather than being an unrelated restatement of the goal."
            )
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    else:
        user_content += "\n\nNo timeframe was given for this goal."
    if opening:
        user_content += (
            "\n\nThis is the opening of a new goal. Your job is to get "
            "enough to write a plan, not to propose a first action to "
            "do right now. Do not set suggested_action. If the goal is "
            "too thin, set clarification to one short question, or set "
            "suggested_duration if a reasonable timeframe default exists."
        )
    return ask_model(DECIDE_SYSTEM_PROMPT, user_content, DECIDE_KEYS)
