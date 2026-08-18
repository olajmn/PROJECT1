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

from backend.goal_to_plan import generate_plan, replan
from backend.storage import HORIZON_LABELS, PLAN_KEYS, get_latest_plan, load_history, save_plan

app = Flask(__name__)

# The horizons shown on the history page, in order, excluding "right_now"
# (which gets its own highlighted box in the template instead of being
# listed alongside the others).
_HISTORY_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]


def render_history_page(history: list[dict]) -> str:
    """
    Render the history page HTML. Shared by the /history route and
    view.py's standalone static-snapshot script, so there's exactly one
    place that knows how to turn history into this page.
    """
    return render_template("history.html", history=history, horizons=_HISTORY_HORIZONS)


@app.route("/")
def index():
    latest = get_latest_plan()
    return render_template("index.html", latest=latest)


@app.route("/goal", methods=["POST"])
def new_goal():
    """Handle the "set a new goal" form: generate a fresh plan and save it."""
    goal = request.form.get("goal", "").strip()
    if goal:
        plan = generate_plan(goal)
        save_plan(goal, plan)
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

    outcome = "Completed the action" if request.form.get("outcome") == "done" else "Did not complete the action"
    note = request.form.get("note", "").strip()
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    new_plan = replan(latest["goal"], latest["plan"], feedback_text)
    save_plan(latest["goal"], new_plan, feedback=feedback_text)
    return redirect(url_for("index"))


@app.route("/history")
def history():
    return render_history_page(load_history())


if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
