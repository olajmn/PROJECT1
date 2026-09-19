"""
Small, direct checks for content-SUGGEST confirmation (`suggested_action`,
added 2026-09-08) - same style as
backend/store/test_data_persistence.py: asserts run top to
bottom, not a test framework. See docs/planning-model.md's ASK vs.
SUGGEST for the semantics being verified here.

Runs entirely against a temporary directory (never the real data/), and
never calls the real Ollama model for Stage 3 Decide/Fill or step
trees - decide.ask_model, generate_plan.ask_model (Fill), and
generate_structure are monkeypatched. These checks verify the WIRING
(which branch runs, what gets carried forward, what gets saved), not
live model wording.

Run from app/:
    .venv/bin/python -m backend.project.engine.plan.test_planner
"""

import shutil
import tempfile
from pathlib import Path

from backend.store import data_persistence as dp
from backend.project.panes.chat.feedback.route_note import route_note
from backend.project.panes.create import resolver
from backend.project.panes.create.lifecycle import create_goal
from backend.project.engine.plan import decide as decide_mod
from backend.project.engine.plan import generate_plan as generate_plan_mod
from backend.project.engine.plan import planner


def _pending_suggestion(vision_id=None):
    """A saved record with suggested_action, via generate_plan() not
    create_goal() - opening mints refuse that field."""
    plan = planner.generate_plan(GOAL_TEXT)
    return dp.save_plan(GOAL_TEXT, plan, duration=None, frozen_duration=None, vision_id=vision_id)

_original_data_dir = dp.DATA_DIR
_original_plans_file = dp.PLANS_FILE
_original_legacy_plans = dp.LEGACY_PLANS_FILE
_original_visions_file = dp.VISIONS_FILE
_original_decide_ask = decide_mod.ask_model
_original_fill_ask = generate_plan_mod.ask_model
_original_generate_structure = generate_plan_mod.generate_structure
_original_replan = planner.replan

_tmp_dir = Path(tempfile.mkdtemp(prefix="planner_test_"))
dp.DATA_DIR = _tmp_dir
dp.PLANS_FILE = _tmp_dir / "plans.jsonl"
dp.LEGACY_PLANS_FILE = _tmp_dir / "plans.json"
dp.VISIONS_FILE = _tmp_dir / "visions.json"
# Never hit Ollama for calendar step trees in these wiring checks.
generate_plan_mod.generate_structure = lambda *args, **kwargs: None

GOAL_TEXT = "I want to get my job search organized and get a job in development"
SUGGESTION_TEXT = "Create a list of your current job-search tasks and prioritize them."


def _canned(response: dict):
    """A fake ask_model() that ignores its arguments and always returns
    (a copy of) `response` - keeps these checks independent of whatever
    the real model would actually say."""
    def _fake(system_prompt, user_content, required_keys):
        return dict(response)
    return _fake


_BLANK_PLAN = {
    "clarification": None, "suggested_action": None, "suggested_duration": None,
    "year": None, "month": None, "week": None, "today": None,
    "hour": None, "minute": None, "now": None,
}


def _set_stage3(response: dict) -> None:
    """One combined-shaped canned dict → Decide stub + Fill stub.
    ASK/SUGGEST never call Fill; PLAN uses Fill for horizons."""
    decide_mod.ask_model = _canned({
        "clarification": response.get("clarification"),
        "suggested_action": response.get("suggested_action"),
        "suggested_duration": response.get("suggested_duration"),
    })
    generate_plan_mod.ask_model = _canned({
        "year": response.get("year"),
        "month": response.get("month"),
        "week": response.get("week"),
        "today": response.get("today"),
        "hour": response.get("hour"),
        "minute": response.get("minute"),
        "now": response.get("now"),
    })


try:
    # ------------------------------------------------------------------
    # generate_plan(): suggested_action validation/priority
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT})
    plan = planner.generate_plan(GOAL_TEXT)
    assert plan["suggested_action"] == SUGGESTION_TEXT
    assert plan["clarification"] is None
    assert plan["now"] is None
    assert plan["steps"] is None

    # Decide never returns horizons; a leaked `now` on a combined-shaped
    # stub must not appear on the plan when suggested_action wins.
    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT, "now": "Do the thing right now"})
    plan = planner.generate_plan(GOAL_TEXT)
    assert plan["now"] is None, "suggested_action must clear a leaked `now`"

    # clarification wins if the model somehow sets both.
    _set_stage3({**_BLANK_PLAN, "clarification": "What does organized mean to you?", "suggested_action": SUGGESTION_TEXT})
    plan = planner.generate_plan(GOAL_TEXT)
    assert plan["clarification"] == "What does organized mean to you?"
    assert plan["suggested_action"] is None

    # suggested_action wins over suggested_duration if the model somehow
    # sets both - resolving what to do first matters before discussing
    # how long it should take.
    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT, "suggested_duration": "8 weeks"})
    plan = planner.generate_plan(GOAL_TEXT)
    assert plan["suggested_action"] == SUGGESTION_TEXT
    assert plan["suggested_duration"] is None

    # A malformed suggested_action (wrong type) is discarded; Fill then
    # runs as planable and may supply `now`.
    _set_stage3({**_BLANK_PLAN, "suggested_action": 12345, "now": "Something to do"})
    plan = planner.generate_plan(GOAL_TEXT)
    assert plan["suggested_action"] is None

    print("OK - generate_plan() suggested_action validation/priority")

    # create_goal() opening cannot land on an Action (suggested_action).
    # Missing timeframe no longer blocks a planable mint — End clarity
    # is Decide's job; co-build does not wait on a span.
    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT})
    opened = create_goal("I want to start working out", "", "")
    assert opened["plan"]["suggested_action"] is None
    assert opened["plan"]["clarification"]
    _set_stage3({**_BLANK_PLAN, "now": "Choose any piece of equipment and begin immediately"})
    opened_now = create_goal("start working out", "", "")
    assert opened_now["plan"]["now"] == "Choose any piece of equipment and begin immediately"
    assert opened_now["plan"]["clarification"] is None
    print("OK - create_goal() opening refuses Action; allows planable without duration")

    # ------------------------------------------------------------------
    # Test 1 - SUGGEST -> "Yes" -> accepted as the current Action
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT})
    pending = _pending_suggestion()
    assert pending["plan"]["suggested_action"] == SUGGESTION_TEXT
    history_before = len(dp.load_history())

    accepted = route_note(pending, "Yes.")
    assert accepted["plan"]["now"] == SUGGESTION_TEXT
    assert accepted["plan"]["suggested_action"] is None
    assert accepted["plan"]["clarification"] is None
    assert accepted["completed"] is False
    assert accepted["project_id"] == pending["project_id"]
    assert accepted["current_step"] == pending.get("current_step", 0)
    assert accepted["step_status"] == pending.get("step_status")
    assert accepted["vision_id"] == pending["vision_id"]
    assert len(dp.load_history()) == history_before + 1, "confirmation must append, not overwrite"

    print("OK - Test 1: SUGGEST -> Yes accepts the suggestion as the current Action")

    # ------------------------------------------------------------------
    # Test 4 - SUGGEST -> Yes -> Action -> "Done" -> existing completion flow
    # ------------------------------------------------------------------

    planner.replan = lambda goal, history, feedback, duration=None, vision_id=None: {
        **_BLANK_PLAN, "now": "Send one application",
    }
    done = route_note(accepted, "Done.")
    assert done["plan"]["now"] == "Send one application", "an ordinary completion report must still call replan()"
    assert done["feedback"].startswith("Completed the action."), done["feedback"]
    planner.replan = _original_replan

    print("OK - Test 4: SUGGEST -> Yes -> Done still runs the existing completion/replan flow")

    # ------------------------------------------------------------------
    # Test 2 - SUGGEST -> explicit alternative ("I'd rather start with my CV")
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT})
    pending2 = _pending_suggestion()

    _set_stage3({**_BLANK_PLAN, "now": "Update the CV's summary section"})
    alt = route_note(pending2, "I'd rather start with my CV.")
    assert alt["plan"]["now"] == "Update the CV's summary section"
    assert alt["plan"]["suggested_action"] is None, "the original suggestion must not be forced through"
    assert alt["feedback"] == "I'd rather start with my CV."

    print("OK - Test 2: SUGGEST -> explicit alternative is not forced through")

    # ------------------------------------------------------------------
    # Test 3 - SUGGEST -> Current State correction ("No, I already have a list")
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "suggested_action": SUGGESTION_TEXT})
    pending3 = _pending_suggestion()

    _set_stage3({**_BLANK_PLAN, "clarification": "Which job boards or contacts does your list already cover?"})
    corrected = route_note(pending3, "No, I already have a list.")
    assert corrected["plan"]["now"] is None
    assert corrected["completed"] is False, "a premise correction must never be read as Action completion"
    assert corrected["plan"]["clarification"] == "Which job boards or contacts does your list already cover?"

    print("OK - Test 3: SUGGEST -> Current State correction is not misread as completion")

    # ------------------------------------------------------------------
    # Test 5 - ordinary Action -> "Yes" still means completed (unaffected)
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "now": "Send four applications"})
    ordinary = create_goal("Send four job applications this week", "", "")
    assert ordinary["plan"]["now"] == "Send four applications"
    assert ordinary["plan"]["suggested_action"] is None

    planner.replan = lambda goal, history, feedback, duration=None, vision_id=None: {
        **_BLANK_PLAN, "now": "Send the next application",
    }
    completed = route_note(ordinary, "Yes.")
    assert completed["feedback"].startswith("Completed the action."), completed["feedback"]
    assert completed["plan"]["now"] == "Send the next application"
    planner.replan = _original_replan

    print("OK - Test 5: an ordinary Action's \"Yes\" is still read as completed")

    # ------------------------------------------------------------------
    # Test 6 - existing suggested_duration flow unaffected
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "suggested_duration": "8 weeks"})
    duration_pending = create_goal("I want to start exercising regularly", "", "")
    assert duration_pending["plan"]["suggested_duration"] == "8 weeks"
    assert duration_pending["plan"]["suggested_action"] is None

    _set_stage3({**_BLANK_PLAN, "today": "Do one session", "now": "Put on your shoes and go for a walk"})
    duration_confirmed = route_note(duration_pending, "Yes, 8 weeks works.")
    assert duration_confirmed["duration"] == "8 weeks"
    assert duration_confirmed["plan"]["now"] == "Put on your shoes and go for a walk"

    print("OK - Test 6: existing suggested_duration flow still works unchanged")

    # ------------------------------------------------------------------
    # Test 7 - existing clarification flow unaffected
    # ------------------------------------------------------------------

    _set_stage3({**_BLANK_PLAN, "clarification": "What do you want to read?"})
    vague = create_goal("read", "", "")
    assert vague["plan"]["clarification"] == "What do you want to read?"

    _set_stage3({**_BLANK_PLAN, "now": "Open the book and read one chapter"})
    answered = route_note(vague, "A novel, for 30 minutes today.")
    assert answered["plan"]["clarification"] is None
    assert answered["plan"]["now"] == "Open the book and read one chapter"

    print("OK - Test 7: existing clarification flow still works unchanged")

    # ------------------------------------------------------------------
    # Test 8 - state preservation across confirmation: current_step,
    # step_status, Vision, append-only history
    # ------------------------------------------------------------------

    vision = dp.save_vision("Grow as a professional")
    _set_stage3({**_BLANK_PLAN, "suggested_action": "Take stock of your current applications."})
    v_pending = _pending_suggestion(vision_id=vision["id"])
    assert v_pending["vision_id"] == vision["id"]

    history_before_goal = resolver.get_history_for_goal(v_pending["project_id"])
    v_accepted = route_note(v_pending, "Yes")
    history_after_goal = resolver.get_history_for_goal(v_accepted["project_id"])

    assert v_accepted["vision_id"] == vision["id"], "Vision link must survive confirmation"
    assert v_accepted["current_step"] == 0
    assert v_accepted["step_status"] == v_pending.get("step_status")
    assert len(history_after_goal) == len(history_before_goal) + 1, "confirmation must append exactly one record"
    # Every prior record for this goal, including the pending suggestion
    # itself, must still be present and unmodified.
    assert history_after_goal[:-1] == history_before_goal, "confirmation must never rewrite earlier history"

    print("OK - Test 8: current_step/step_status/Vision/history survive confirmation")

    print()
    print("ALL OK - content-SUGGEST confirmation behaves as expected")
finally:
    decide_mod.ask_model = _original_decide_ask
    generate_plan_mod.ask_model = _original_fill_ask
    generate_plan_mod.generate_structure = _original_generate_structure
    planner.replan = _original_replan
    dp.DATA_DIR = _original_data_dir
    dp.PLANS_FILE = _original_plans_file
    dp.LEGACY_PLANS_FILE = _original_legacy_plans
    dp.VISIONS_FILE = _original_visions_file
    shutil.rmtree(_tmp_dir, ignore_errors=True)
