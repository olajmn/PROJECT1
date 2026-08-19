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

from backend.goal_to_plan import describe_duration, generate_plan, replan
from backend.storage import (
    HORIZON_LABELS,
    PLAN_KEYS,
    get_board,
    get_latest_plan,
    load_history,
    save_plan,
)

app = Flask(__name__)
# Makes describe_duration() callable directly from templates, e.g.
# {{ describe_duration(record.duration) }} in _plan_entry.html/index.html -
# so the "how was this understood" text stays in one place (goal_to_plan.py)
# instead of being duplicated as static strings in the templates.
app.jinja_env.globals["describe_duration"] = describe_duration

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
    latest = get_latest_plan()
    return render_template(
        "index.html",
        latest=latest,
        horizons=_BROADER_HORIZONS,
        history=load_history(),
        board=get_board(),
    )


@app.route("/goal", methods=["POST"])
def new_goal():
    """Handle the "set a new goal" form: generate a fresh plan and save it."""
    goal = request.form.get("goal", "").strip()
    duration = request.form.get("duration", "").strip() or None
    if goal:
        plan = generate_plan(goal, duration)
        save_plan(goal, plan, duration=duration)
    return redirect(url_for("index"))


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle the "how did it go" form: turn the button pressed + optional
    note into a feedback sentence, ask the agent to replan, and save the
    result as a new history entry.
    """
    latest = get_latest_plan()
    if latest is None:
        # Nothing to give feedback on (e.g. a stale tab, or plans.json
        # was cleared while the server was running) - just go back home
        # instead of crashing.
        return redirect(url_for("index"))

    outcome_value = request.form.get("outcome")
    note = request.form.get("note", "").strip()
    duration = latest.get("duration")

    if outcome_value == "goal_done":
        # The whole goal is done, not just this one "right_now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        save_plan(latest["goal"], latest["plan"], feedback=feedback_text, duration=duration, completed=True)
        return redirect(url_for("index"))

    outcome = "Completed the action" if outcome_value == "done" else "Did not complete the action"
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    new_plan = replan(latest["goal"], latest["plan"], feedback_text, duration=duration)
    save_plan(latest["goal"], new_plan, feedback=feedback_text, duration=duration)
    return redirect(url_for("index"))


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
