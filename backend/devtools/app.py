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
from backend.storage import get_latest_plan, load_history, save_plan
from backend.devtools.view import render_html

app = Flask(__name__)


@app.route("/")
def index():
    latest = get_latest_plan()
    return render_template("index.html", latest=latest)


@app.route("/goal", methods=["POST"])
def new_goal():
    """Handle the "set a new goal" form: generate a fresh plan and save it."""
    goal = request.form["goal"]
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

    outcome = "Completed the action" if request.form["outcome"] == "done" else "Did not complete the action"
    note = request.form.get("note", "").strip()
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    new_plan = replan(latest["goal"], latest["plan"], feedback_text)
    save_plan(latest["goal"], new_plan, feedback=feedback_text)
    return redirect(url_for("index"))


@app.route("/history")
def history():
    """Reuse view.py's rendering to show the full history in-browser."""
    return render_html(load_history())


if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
