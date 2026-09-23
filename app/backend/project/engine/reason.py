"""
Revise reasoning from feedback.

First pass is judgment/run_stage3(). This file runs again after a
note: same boxes, new history. Minting is create/lifecycle.py;
id links are create/project_user.py.

Never talks to the model directly (see judgment/ask.py).
The stored `plan` field is still that disk shape — this file is
not named after it.
"""

# Contents
#  1. Frozen duration for save
#      - frozen_duration_for()
#
#  2. Revise
#      - replan()
#      - apply_new_duration()

from backend.foundation.time import freeze_duration, resolve_duration
from backend.store.data_persistence import get_user, save_plan
from backend.project.engine.judgment.run_stage3 import run_stage3
from backend.project.engine.judgment.shape import (
    PLAN_KEYS,
    _horizon_scope_instruction,
)
from backend.project.engine.time.current_time import current_time
from backend.project.engine.judgment.ask import ask
from backend.project.engine.judgment.prompts import REPLAN_SYSTEM_PROMPT


# ============================================================
# 1. Frozen duration for save
# ============================================================


def frozen_duration_for(plan: dict, duration: str | None) -> dict | None:
    """
    The frozen_duration to save alongside `plan` - None while `plan` is
    a clarification or a proposed-but-unconfirmed suggested_duration
    (nothing has actually started yet, so there's no honest countdown
    to freeze), otherwise freeze_duration(duration).
    """
    if plan.get("clarification") or plan.get("suggested_duration") or plan.get("suggested_action"):
        return None
    return freeze_duration(duration)


# ============================================================
# 2. Revise
# ============================================================


def replan(goal: str, history: list[dict], feedback: str, duration: str | None = None, sim_user_id: int | None = None) -> dict:
    """
    Takes the goal, its full history (oldest first), and feedback on
    the most recent "now" action, and asks the model again.
    Returns the same shape as run_stage3().

    Passing the *whole* history, not just the previous record, is what
    lets REPLAN_SYSTEM_PROMPT's "don't shrink 'now' more than once"
    rule work - a model shown only the last step can't notice it has
    already made the same task smaller several times in a row (see
    docs/06-development.md, 2026-08-20, for the drift this fixed).

    `sim_user_id` - same optional background as run_stage3()
    (added 2026-09-06): a project's linked id is meant to follow it
    for its whole lifetime, not just the first pass.
    """
    # Named history_lines, not "steps" - unrelated to the stored
    # `steps` field / calendar.generate_structure(); this is prose
    # for the revise prompt, not the step list.
    history_lines = []
    for record in history:
        right_now = record["plan"].get("now") or "(none)"
        if record.get("feedback"):
            history_lines.append(f'- now: "{right_now}" -> feedback: "{record["feedback"]}"')
        else:
            history_lines.append(f'- now: "{right_now}" (the first pass, no feedback yet)')
    history_text = "\n".join(history_lines)

    user_content = (
        f"The current date and time is: {current_time()}\n\n"
        f"My goal is: {goal}\n\n"
        f"This goal's full history so far, oldest first:\n{history_text}\n\n"
        f"My feedback on the most recent 'now' action: {feedback}"
    )
    if sim_user_id is not None:
        vision = get_user(sim_user_id)
        if vision is not None:
            user_content += (
                f"\n\nThis project is part of a broader direction: "
                f"{vision['text']}"
            )
    if duration:
        user_content += f"\n\nThis plan should still span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    return ask(REPLAN_SYSTEM_PROMPT, user_content, PLAN_KEYS)


def apply_new_duration(existing: dict, duration: str, feedback: str) -> dict:
    """
    Run reasoning again around a new duration span - the shared
    logic behind /feedback's requests_duration_change() flow.

    Always calls run_stage3() rather than patching duration onto
    the existing record: changing the timeframe is a real new
    decision. `existing["sim_user_id"]` is carried forward
    unchanged, same as `project_id`.
    """
    plan = run_stage3(existing["goal"], duration, sim_user_id=existing.get("sim_user_id"))
    return save_plan(
        existing["goal"], plan, feedback=feedback, duration=duration, goal_id=existing["project_id"],
        frozen_duration=frozen_duration_for(plan, duration),
        sim_user_id=existing.get("sim_user_id"),
    )
