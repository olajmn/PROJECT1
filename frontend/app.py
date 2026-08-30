"""
Frontend App
============

Local interactive web interface for the agent - talking to the agent
through a browser instead of running separate terminal scripts. Not a
separate product frontend concept - this IS the interface layer (see
docs/03-architecture.md § Runtime architecture: the UI and backend are
separate layers, interfaces are replaceable clients). Runs 100%
locally, only reachable from this machine, no internet needed.

Contents
1. Setup
2. Routes - overview & vision
3. Routes - goal creation & duration changes
4. Routes - feedback & step tracking
5. Routes - history views
6. CLI entry point

Run from the PROJECT ROOT (not from inside frontend/):
    .venv/bin/python -m frontend.app
The -m flag is required (not `python frontend/app.py`) so the
`from backend...` imports below can find the backend package. Lives as
a top-level sibling of backend/ (this talks TO the agent, it isn't
part of the agent's own cognition - the same category as tools/ and
docs/, not backend/); full history: docs/06-development.md, 2026-08-24.
Moved from devtools/ to frontend/ 2026-08-30, once it had become the
project's actual (if still local-only) web layer rather than a
personal dev tool - see docs/06-development.md for that entry.
"""

from flask import Flask, redirect, render_template, request, url_for

from backend.foundation.time import describe_duration, duration_progress, step_plan
from backend.goals.goal.resolver import get_history_for_goal, get_latest_for_goal
from backend.goals.plan.planner import advance_step, apply_feedback, create_goal
from backend.infrastructure.data_persistence import load_history, load_visions, save_vision
from frontend.view_data.goal_overview import build_goal_overview, group_active_by_vision
from frontend.view_data.plan_horizons import BROADER_HORIZONS
from frontend.view_data.text_formatting import join_plan_prose, split_message_lines

# ============================================================
# 1. Setup
# ============================================================

# template_folder isn't set explicitly - "templates" is Flask's own
# default, and that's this folder's actual name now. static_folder
# stays customized ("css", not the default "static"): Flask serves
# *everything* in that folder as raw downloadable files at
# /static/..., so keeping it separate means only the CSS is exposed
# that way, never app.py itself. The `static` endpoint name and the
# url_for('static', ...) calls in the templates don't change just
# because the on-disk folder does - only WHERE Flask looks, not what
# anything is called from outside.
app = Flask(__name__, static_folder="css")
# Makes describe_duration() callable directly from templates, e.g.
# {{ describe_duration(record.duration) }} in _plan_entry.html/index.html -
# so the "how was this understood" text stays in one place
# (backend/foundation/time/time_logic/duration_resolution.py) instead of being duplicated as static strings
# in the templates.
app.jinja_env.globals["describe_duration"] = describe_duration
# Same reasoning, for the start/now/end progress bar in
# active_goal/_timeperiod.html - percent/status/labels computed once in
# foundation/time/ (see duration_progress()'s docstring), not recomputed
# in template logic.
app.jinja_env.globals["duration_progress"] = duration_progress
# Same reasoning - the vertical step list in active_goal/_task.html and
# active_goal/_steps.html zips a goal's stored step descriptions
# (record.plan.steps, from backend/goals/plan/step_generator.py's generate_steps()) with
# their deterministically-computed time slice via step_plan() - see
# its docstring.
app.jinja_env.globals["step_plan"] = step_plan
# Same reasoning: lets active_goal/_conversation.html pull a goal's whole
# conversation (see get_history_for_goal's docstring) without every
# route that renders it having to fetch and pass that separately.
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal
# Same reasoning as the globals above - joins Plan's filled-horizon
# sentences into one flowing paragraph (see active_goal/_plan.html)
# rather than a bare space-join done in the template itself.
app.jinja_env.globals["join_plan_prose"] = join_plan_prose
# Registered as a filter (`{{ text | split_message_lines }}`), not a
# global like the others above - this transforms a string that's
# already in template scope (msg.feedback, msg.right_now, ...) rather
# than pulling in data the template doesn't have yet, so filter syntax
# reads more naturally at every call site.
app.jinja_env.filters["split_message_lines"] = split_message_lines

# ============================================================
# 2. Routes - overview & vision
# ============================================================


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
    """
    Handle the "set a vision" form: save a new Vision and return to the
    goal overview. Create-only - see save_vision()'s docstring for why editing/
    deleting an existing one isn't built yet.

    Deliberately does not attach itself to any goal - a Vision exists
    independently first (see docs/03-architecture.md § Vision: it
    "provides optional context to multiple Goals", it isn't itself the
    first step of a pipeline). Attaching one to a goal
    happens in /goal's own form instead, via `vision_id`/`new_vision`.
    """
    text = request.form.get("text", "").strip()
    if text:
        save_vision(text)
    return redirect(url_for("index"))


# ============================================================
# 3. Routes - goal creation & duration changes
# ============================================================


@app.route("/goal", methods=["POST"])
def new_goal():
    """
    Handle the "set a goal" form: read the typed goal and optional
    Vision fields, and let planner.create_goal() decide and save the
    new goal's initial plan (or clarification round). See that
    function's docstring for the actual decision logic. Redirects
    straight to the new goal's own card (`#goal-{id}`, same anchor
    apply_feedback() uses) so a pending clarification is immediately
    visible, not buried below the fold.
    """
    typed_text = request.form.get("goal", "").strip()
    if not typed_text:
        return redirect(url_for("index"))

    record = create_goal(
        typed_text,
        request.form.get("new_vision", "").strip(),
        request.form.get("vision_id", "").strip(),
    )
    return redirect(url_for("index") + f"#goal-{record['goal_id']}")


# ============================================================
# 4. Routes - feedback & step tracking
# ============================================================


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle the "what's going on" form: read which goal and what note
    was typed, and let planner.apply_feedback() decide and persist the
    actual state transition. See that function's docstring for the
    full decision logic (clarification answers, duration questions,
    outcome classification, and replanning).
    """
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        # Bad/missing goal_id (e.g. a stale tab, or the goal was
        # completed in another tab since this page loaded) - just go
        # back home instead of crashing or guessing which goal to act on.
        return redirect(url_for("index"))

    apply_feedback(latest, request.form.get("note", "").strip())
    # Redirect back to this specific goal's own card (see
    # _active_goal.html's id="goal-{{ goal_id }}"), not just "/" - a
    # goal's thread only ever grows, so reloading straight to the top of
    # the page buries the message that just confirms the click actually
    # registered below however much history came before it (2026-08-20,
    # see docs/06-development.md): without it, repeated "Still working
    # on it" clicks look broken for exactly this reason - the save
    # always worked, the confirmation was just scrolled out of view.
    return redirect(url_for("index") + f"#goal-{latest['goal_id']}")


@app.route("/step", methods=["POST"])
def step():
    """
    Handle the per-step "Done?" Yes/No control (see active_goal/_task.html)
    - reads which goal and whether the step was marked done, and lets
    planner.advance_step() decide and persist the actual change. See
    that function's docstring for the step-advancement logic itself.
    """
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        return redirect(url_for("index"))

    advance_step(latest, request.form.get("done") == "yes")
    return redirect(url_for("index") + f"#goal-{latest['goal_id']}")


# ============================================================
# 5. Routes - history views
# ============================================================


@app.route("/history")
def history():
    return render_template("goal_log/history.html", history=load_history(), horizons=BROADER_HORIZONS)


@app.route("/completed")
def completed():
    """
    Completed goals only, on their own page - index.html already shows
    Active, so a second page repeating it never earned its keep.
    build_goal_overview() still computes both halves (it groups ALL
    history by goal_id, splitting into active/completed is just what
    falls out of that in one pass) but only the completed half is ever
    read here now, via completed_goal/_completed.html (passed to the
    template as `board.completed`, its unchanged template-facing name).
    """
    return render_template("completed_goal/completed.html", board=build_goal_overview(), horizons=BROADER_HORIZONS)


# ============================================================
# 6. CLI entry point
# ============================================================

if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
