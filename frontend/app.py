"""
Frontend App

Local web interface for the agent.

Run from the project root:
    .venv/bin/python -m frontend.app

The -m flag is required so the backend package can be imported correctly.
See docs/06-development.md for development history.
"""

from flask import Flask, redirect, render_template, request, url_for

from backend.foundation.time import describe_duration, duration_progress, step_plan
from backend.goals.goal.resolver import get_history_for_goal, get_latest_for_goal
from backend.goals.plan.planner import advance_step, apply_feedback, create_goal
from backend.infrastructure.data_persistence import load_history, load_visions, save_vision
from frontend.view_data.goal_overview import build_goal_overview, group_active_by_vision
from frontend.view_data.plan_horizons import BROADER_HORIZONS
from frontend.view_data.text_formatting import join_plan_prose, split_message_lines

# Flask setup

# "css", not Flask's default "static/" - everything in that folder is
# served as raw downloadable files, so keeping it separate avoids
# exposing anything but the CSS that way.
app = Flask(__name__, static_folder="css")

# Register backend/view-data helpers used directly by templates,
# keeping presentation logic out of the templates themselves.
app.jinja_env.globals["describe_duration"] = describe_duration
app.jinja_env.globals["duration_progress"] = duration_progress
app.jinja_env.globals["step_plan"] = step_plan
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal
app.jinja_env.globals["join_plan_prose"] = join_plan_prose
# A filter because it transforms a value already in template scope.
app.jinja_env.filters["split_message_lines"] = split_message_lines


@app.route("/")
def index():
    goal_overview = build_goal_overview()
    visions = load_visions()
    return render_template(
        "index.html",
        horizons=BROADER_HORIZONS,
        history=load_history(),
        board=goal_overview,  # template-facing name, unchanged - see index.html
        visions=visions,
        vision_groups=group_active_by_vision(goal_overview["active"], visions),
    )


@app.route("/vision", methods=["POST"])
def new_vision():
    """A Vision exists independently of a goal (docs/03-architecture.md § Vision) - attaching one happens in /goal."""
    text = request.form.get("text", "").strip()
    if text:
        save_vision(text)
    return redirect(url_for("index"))


@app.route("/goal", methods=["POST"])
def new_goal():
    """planner.create_goal() owns the decision logic."""
    typed_text = request.form.get("goal", "").strip()
    if not typed_text:
        return redirect(url_for("index"))

    record = create_goal(
        typed_text,
        request.form.get("new_vision", "").strip(),
        request.form.get("vision_id", "").strip(),
    )
    # Anchored so a pending clarification is visible immediately.
    return redirect(url_for("index") + f"#goal-{record['goal_id']}")


@app.route("/feedback", methods=["POST"])
def feedback():
    """planner.apply_feedback() owns the decision logic."""
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        # Stale tab, or the goal was completed elsewhere - go home rather than guess.
        return redirect(url_for("index"))

    apply_feedback(latest, request.form.get("note", "").strip())
    # Anchored so new feedback stays visible in a growing thread (docs/06-development.md).
    return redirect(url_for("index") + f"#goal-{latest['goal_id']}")


@app.route("/step", methods=["POST"])
def step():
    """planner.advance_step() owns the decision logic."""
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        return redirect(url_for("index"))

    advance_step(latest, request.form.get("done") == "yes")
    return redirect(url_for("index") + f"#goal-{latest['goal_id']}")


@app.route("/history")
def history():
    return render_template("goal_log/history.html", history=load_history(), horizons=BROADER_HORIZONS)


@app.route("/completed")
def completed():
    """index.html shows active goals; this route uses only the completed half of build_goal_overview()."""
    return render_template("completed_goal/completed.html", board=build_goal_overview(), horizons=BROADER_HORIZONS)


if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service.
    app.run(host="127.0.0.1", port=5050, debug=True)
