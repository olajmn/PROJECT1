"""
Local interactive web interface for the agent.

This is a personal dev tool for talking to the agent through a browser
instead of running separate terminal scripts - NOT the product's real
frontend (see docs/08-technical-architecture.md "Frontend direction").
Runs 100% locally, only reachable from this machine, no internet needed.

Run from the PROJECT ROOT (not from inside backend/ or backend/devtools/):
    .venv/bin/python -m backend.devtools.app
The -m flag is required (not `python backend/devtools/app.py`) so the
`from backend...` imports below can find the backend package.
"""

from flask import Flask, redirect, render_template, request, url_for

from backend.goal import get_board, get_history_for_goal, get_latest_for_goal
from backend.outcome_classifier import classify_outcome
from backend.plan import HORIZON_LABELS, PLAN_KEYS, generate_plan, replan
from backend.storage import load_history, save_plan
from backend.timeperiod import describe_duration

app = Flask(__name__)
# Makes describe_duration() callable directly from templates, e.g.
# {{ describe_duration(record.duration) }} in _plan_entry.html/index.html -
# so the "how was this understood" text stays in one place
# (backend/timeperiod.py) instead of being duplicated as static strings
# in the templates.
app.jinja_env.globals["describe_duration"] = describe_duration
# Same reasoning: lets _active_goal.html pull a goal's whole
# conversation (see get_history_for_goal's docstring) without every
# route that renders it having to fetch and pass that separately.
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal

# The broader horizons shown alongside "right_now", on both the index
# page and the history page, in order, excluding "right_now" itself
# (which always gets its own highlighted box instead of being listed
# alongside the others). A goal with a short duration will have these
# come back as null/None - the templates skip any horizon that's falsy,
# so only the levels actually relevant to the goal show up.
_BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]


def render_history_page(history: list[dict]) -> str:
    """
    Render the history page HTML. Shared by the /history route and
    view.py's standalone static-snapshot script, so there's exactly one
    place that knows how to turn history into this page.
    """
    return render_template("history.html", history=history, horizons=_BROADER_HORIZONS)


@app.route("/")
def index():
    return render_template(
        "index.html",
        horizons=_BROADER_HORIZONS,
        history=load_history(),
        board=get_board(),
    )


@app.route("/goal", methods=["POST"])
def new_goal():
    """
    Handle the "set a goal" form: generate a fresh plan and save it.

    The form lets the user pick an existing active goal to continue
    (via `continue_goal_id`) instead of typing its text again - typing
    is how goals used to fragment (see backend/goal.py's get_board()). When
    continuing, the existing goal's own text is reused as-is and the
    goal_id is carried forward, so this record joins that goal's chain
    instead of starting a new one. A genuinely new goal (no selection)
    still requires typed `goal` text, and mints its own goal_id via
    save_plan().
    """
    continue_goal_id = request.form.get("continue_goal_id", "").strip()
    duration = request.form.get("duration", "").strip() or None

    if continue_goal_id:
        existing = next(
            (r for r in get_board()["active"] if str(r["goal_id"]) == continue_goal_id),
            None,
        )
        if existing is None:
            # Stale selection (e.g. the goal was completed in another tab
            # since this page loaded) - nothing sensible to continue.
            return redirect(url_for("index"))
        plan = generate_plan(existing["goal"], duration)
        save_plan(existing["goal"], plan, duration=duration, goal_id=existing["goal_id"])
        return redirect(url_for("index"))

    goal = request.form.get("goal", "").strip()
    if goal:
        plan = generate_plan(goal, duration)
        save_plan(goal, plan, duration=duration)
    return redirect(url_for("index"))


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle the "what's going on" form: classify the free-text note into
    an outcome (see backend/outcome_classifier.py - no LLM, recognized
    phrases only), then act on it exactly as the old Yes/Still working
    on it/No/Goal complete buttons used to. There's no separate
    "outcome" field anymore - the note itself is the only signal, so
    typing doesn't mean picking which of four boxes your situation
    best fits; see docs/12-decisions.md, 2026-08-20, for why this
    replaced the buttons and why it still never lets an LLM decide
    true/false.

    Which goal this applies to comes from the form's `goal_id` (each
    active board card posts its own) - not "whatever was touched most
    recently overall". With more than one active goal on the board at
    once, that distinction is the difference between feedback landing
    on the goal you actually meant versus a different one entirely.
    """
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        # Bad/missing goal_id (e.g. a stale tab, or the goal was
        # completed in another tab since this page loaded) - just go
        # back home instead of crashing or guessing which goal to act on.
        return redirect(url_for("index"))

    note = request.form.get("note", "").strip()
    duration = latest.get("duration")
    classified = classify_outcome(note)
    # Anything not confidently recognized defaults to the same safe
    # no-op as "in_progress" - check in without changing the plan,
    # rather than guess toward a riskier outcome (done/goal_done) from
    # ambiguous text. See classify_outcome()'s docstring.
    outcome_value = classified or "in_progress"

    # Redirect back to this specific goal's own card (see
    # _active_goal.html's id="goal-{{ goal_id }}"), not just "/" - a
    # goal's thread only ever grows, so reloading straight to the top of
    # the page buries the message that just confirms the click actually
    # registered below however much history came before it. Found via
    # real use, 2026-08-20 (see docs/11-experiments.md): repeated
    # "Still working on it" clicks looked broken for exactly this reason
    # - the save always worked, the confirmation was just scrolled out
    # of view.
    back_to = redirect(url_for("index") + f"#goal-{latest['goal_id']}")

    if outcome_value == "goal_done":
        # The whole goal is done, not just this one "right_now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
        )
        return back_to

    if outcome_value == "in_progress":
        # Mid-task, not stalled or failed - a real, distinct signal from
        # "No" (see docs/11-experiments.md, 2026-08-20): three rapid
        # "not done" clicks in a row, each meant as "still working on
        # it", instead shrank the task further each time (30 min -> 15
        # min -> 5 min, "without even taking a note") because replan()
        # was told "not done" and reasonably tried to make it easier.
        # No replan() call here on purpose - check in without asking
        # the model to change anything, so the plan can't drift just
        # because time passed. `classified` distinguishes "you said
        # you're still working on it" from "we genuinely couldn't tell"
        # - both get the same safe treatment, but the record should be
        # honest about which one actually happened.
        prefix = "Still working on it." if classified else "Checked in (couldn't tell what this means yet)."
        feedback_text = prefix + (f" Note: {note}" if note else "")
        save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, goal_id=latest["goal_id"],
        )
        return back_to

    outcome = "Completed the action" if outcome_value == "done" else "Did not complete the action"
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    # The full chain, not just latest["plan"] - see replan()'s docstring
    # for why: a model only shown the single previous step has no way to
    # notice it has already shrunk right_now several times in a row.
    new_plan = replan(latest["goal"], get_history_for_goal(latest["goal_id"]), feedback_text, duration=duration)
    # goal_id carried forward explicitly - without this, save_plan() would
    # mint a fresh one and this replan would silently start a *new* board
    # entry instead of continuing the existing goal's chain.
    save_plan(latest["goal"], new_plan, feedback=feedback_text, duration=duration, goal_id=latest["goal_id"])
    return back_to


@app.route("/history")
def history():
    return render_history_page(load_history())


@app.route("/board")
def board():
    return render_template("board.html", board=get_board(), horizons=_BROADER_HORIZONS)


if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
