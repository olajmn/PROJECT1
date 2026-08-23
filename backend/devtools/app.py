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
from backend.plan import HORIZON_LABELS, PLAN_KEYS, generate_plan, join_plan_prose, replan
from backend.storage import load_history, save_plan
from backend.timeperiod import (
    describe_duration,
    duration_progress,
    extract_duration_phrase,
    freeze_duration,
    step_plan,
)

app = Flask(__name__)
# Makes describe_duration() callable directly from templates, e.g.
# {{ describe_duration(record.duration) }} in _plan_entry.html/index.html -
# so the "how was this understood" text stays in one place
# (backend/timeperiod.py) instead of being duplicated as static strings
# in the templates.
app.jinja_env.globals["describe_duration"] = describe_duration
# Same reasoning, for the start/now/end progress bar in
# _active_goal.html - percent/status/labels computed once in
# timeperiod.py (see duration_progress()'s docstring), not recomputed
# in template logic.
app.jinja_env.globals["duration_progress"] = duration_progress
# Same reasoning - the vertical step list in _active_goal.html zips a
# goal's stored step descriptions (record.plan.steps, from
# backend/plan.py's _generate_steps()) with their deterministically-
# computed time slice via step_plan() - see its docstring.
app.jinja_env.globals["step_plan"] = step_plan
# Same reasoning: lets _active_goal.html pull a goal's whole
# conversation (see get_history_for_goal's docstring) without every
# route that renders it having to fetch and pass that separately.
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal
# Same reasoning - joins Plan's filled-horizon sentences into one
# flowing paragraph (see _active_goal.html's Plan section, 2026-08-23)
# rather than a bare space-join done in the template itself.
app.jinja_env.globals["join_plan_prose"] = join_plan_prose

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

    One text field now (2026-08-23; used to be two - goal and duration
    typed separately) - `extract_duration_phrase()`
    (backend/timeperiod.py) searches whatever was typed for a
    recognized time phrase anywhere inside it (e.g. "clean the
    apartment this weekend"), the same matchers a dedicated duration
    field already used, just applied to the whole sentence instead of
    a field reserved for only that. If NOTHING recognized turns up at
    all, that's treated as "no timeframe given" DETERMINISTICALLY,
    before even calling the model - a fixed clarifying-question round
    is saved asking for one, same "code decides, model is just told"
    reasoning as the horizon-scope fix (see plan.py's
    _horizon_scope_instruction()) rather than relying on the model to
    reliably notice this itself (see docs/12-decisions.md, 2026-08-23,
    for why the model isn't trusted with judgment calls like this one
    when code can decide them outright).

    The form lets the user pick an existing active goal to continue
    (via `continue_goal_id`) instead of typing its text again - typing
    is how goals used to fragment (see backend/goal.py's get_board()).
    When continuing, the existing goal's own text is reused as-is and
    the goal_id is carried forward, so this record joins that goal's
    chain instead of starting a new one; whatever's typed in the (now
    single, always-enabled) text field in that case is read as a NEW
    duration only, not new goal text - see index.html. Nothing typed
    means "keep going with whatever timeframe was already running" -
    the existing goal's own last-known duration carries forward
    unchanged, same as a plain check-in via /feedback would, not
    silently dropped just because the field was left empty.

    A genuinely new goal (no selection) still requires typed text, and
    mints its own goal_id via save_plan().

    Both paths compute a FRESH `frozen_duration` (see
    backend/timeperiod.py's freeze_duration()) only when there's an
    actual new duration decision to freeze (a new goal, or an explicit
    "continue" with a NEW duration typed) - an explicit "continue" with
    nothing typed reuses the existing goal's own frozen_duration
    unchanged, same reasoning /feedback's check-in path already
    follows: continuing without saying otherwise isn't a new planning
    decision, so it shouldn't restart the countdown. EXCEPT when
    `generate_plan()` comes back with `clarification` set instead of a
    real plan (see that function's docstring) - the goal as typed was
    too vague in CONTENT (a bare noun/verb, e.g. "read") to plan at
    all, a different case from missing TIME above. That round is saved
    too (as a new active board entry, or a new round on an existing
    one) so the question shows up in the goal's own conversation thread
    and the user can answer it right there via the normal feedback box
    - see /feedback below, which is what actually resolves a pending
    clarification into a real plan. But its `frozen_duration` is left
    None rather than frozen now: nothing has actually started yet
    while a question is still pending, so there's no honest countdown
    to draw until /feedback resolves it into a real plan and freezes it
    then. Redirects straight to the card either way (`#goal-{id}`, same
    anchor /feedback uses) so the question is immediately visible, not
    buried below the fold.
    """
    continue_goal_id = request.form.get("continue_goal_id", "").strip()
    typed_text = request.form.get("goal", "").strip()

    if continue_goal_id:
        existing = next(
            (r for r in get_board()["active"] if str(r["goal_id"]) == continue_goal_id),
            None,
        )
        if existing is None:
            # Stale selection (e.g. the goal was completed in another tab
            # since this page loaded) - nothing sensible to continue.
            return redirect(url_for("index"))
        new_duration = extract_duration_phrase(typed_text) if typed_text else None
        duration = new_duration or existing.get("duration")
        frozen = freeze_duration(duration) if new_duration else existing.get("frozen_duration")
        plan = generate_plan(existing["goal"], duration)
        record = save_plan(
            existing["goal"], plan, duration=duration, goal_id=existing["goal_id"],
            frozen_duration=None if plan.get("clarification") else frozen,
        )
        return redirect(url_for("index") + f"#goal-{record['goal_id']}")

    if typed_text:
        duration = extract_duration_phrase(typed_text)
        if duration is None:
            # Nothing recognized as a timeframe anywhere in what was
            # typed - ask, deterministically, without spending a model
            # call to find that out. Every other horizon stays JSON
            # null (nothing planned yet), matching the shape a
            # content-vagueness clarification from generate_plan()
            # already has (see that function's docstring).
            clarification_plan = {key: None for key in PLAN_KEYS}
            clarification_plan["clarification"] = "When do you want to do this, or how long should it take?"
            clarification_plan["steps"] = None
            record = save_plan(typed_text, clarification_plan, duration=None, frozen_duration=None)
            return redirect(url_for("index") + f"#goal-{record['goal_id']}")
        plan = generate_plan(typed_text, duration)
        record = save_plan(
            typed_text, plan, duration=duration,
            frozen_duration=None if plan.get("clarification") else freeze_duration(duration),
        )
        return redirect(url_for("index") + f"#goal-{record['goal_id']}")
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

    if latest["plan"].get("clarification"):
        # This goal has no real plan yet - the agent asked a clarifying
        # question instead (see backend/plan.py's generate_plan()
        # docstring), and `note` is the ANSWER to that question, not a
        # status report on a task that doesn't exist yet. Route it
        # through generate_plan() again (not replan(), which is built
        # entirely around "did you complete right_now" - there is no
        # right_now here to have completed), never through
        # classify_outcome() below: an answer like "speed and
        # comprehension" isn't a done/not-done/in-progress signal at
        # all, forcing it through that classifier would be a category
        # error, not just an inaccurate guess.
        #
        # Every prior answer in this goal's history rides along too,
        # not just this latest note - same reasoning replan() passing
        # the FULL history (not just the last round) already follows:
        # a two-round clarification ("what aspect?" -> "speed" -> "how
        # much time do you have?" -> "20 min") needs both answers
        # together, or the second call would re-ask something the first
        # answer already covered. Every record in this goal's history
        # is guaranteed to be a clarification round (this branch only
        # ever runs while `clarification` keeps coming back), so every
        # past `feedback` here really is a prior answer, safe to join
        # as-is.
        prior_answers = [r["feedback"] for r in get_history_for_goal(latest["goal_id"]) if r.get("feedback")]
        combined_goal = " - ".join([latest["goal"], *prior_answers, note])
        plan = generate_plan(combined_goal, duration)
        # frozen_duration stays None for as long as clarification keeps
        # coming back (same reasoning as /goal above: nothing has
        # actually started yet) - only frozen for real, for the first
        # time, the moment a real plan finally comes back.
        save_plan(
            latest["goal"], plan, feedback=note, duration=duration,
            goal_id=latest["goal_id"],
            frozen_duration=None if plan.get("clarification") else freeze_duration(duration),
        )
        return back_to

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # backend/timeperiod.py's freeze_duration() and
    # backend/storage.py's save_plan() docstring for why re-deriving
    # this from "now" here was the actual bug). Falls back to computing
    # one fresh only for a goal saved before frozen_duration existed
    # (2026-08-21) - a one-time "adopt now" so it isn't permanently
    # stuck without a bar, not a recurring recompute.
    frozen = latest.get("frozen_duration") or freeze_duration(duration)
    classified = classify_outcome(note)
    # Anything not confidently recognized defaults to the same safe
    # no-op as "in_progress" - check in without changing the plan,
    # rather than guess toward a riskier outcome (done/goal_done) from
    # ambiguous text. See classify_outcome()'s docstring.
    outcome_value = classified or "in_progress"

    if outcome_value == "goal_done":
        # The whole goal is done, not just this one "right_now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
            frozen_duration=frozen,
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
            duration=duration, goal_id=latest["goal_id"], frozen_duration=frozen,
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
    save_plan(
        latest["goal"], new_plan, feedback=feedback_text, duration=duration,
        goal_id=latest["goal_id"], frozen_duration=frozen,
    )
    return back_to


@app.route("/step", methods=["POST"])
def step():
    """
    Handle the per-step "Done?" Yes/No control (see _active_goal.html) -
    advances `current_step` by one, purely by index arithmetic into the
    goal's already-generated `plan.steps` list. No model call at all:
    unlike /feedback's free-text note (which can trigger replan() -
    the model reconsidering the plan), the step list was already fully
    decided upfront (see backend/plan.py's _generate_steps()), so
    moving through it is just "which one are we on now", nothing to
    ask the model about.

    "No" doesn't move the pointer - it's logged the same safe,
    no-replan way /feedback's "in_progress" is, so a step can't be
    silently reworded/shrunk just because it wasn't done yet either.

    `current_step` can reach `len(steps)` (one past the last valid
    index, not a real step) to mean "every step is done" - see
    _active_goal.html for how that's shown (no more Yes/No, a prompt to
    mark the whole goal complete via the existing free-text box
    instead, not an automatic completion this route decides on its
    own).
    """
    goal_id_value = request.form.get("goal_id", "").strip()
    latest = get_latest_for_goal(int(goal_id_value)) if goal_id_value else None
    if latest is None:
        return redirect(url_for("index"))

    back_to = redirect(url_for("index") + f"#goal-{latest['goal_id']}")
    steps = latest["plan"].get("steps")
    if not steps:
        # Nothing to advance - no step list on this goal at all (see
        # backend/plan.py's generate_plan(): only goals with a
        # resolvable duration get one).
        return back_to

    current = latest.get("current_step", 0)
    if current >= len(steps):
        # Already at "all steps done" - nothing left to confirm.
        return back_to

    if request.form.get("done") == "yes":
        next_index = current + 1
        if next_index >= len(steps):
            feedback_text = f"Completed step {current + 1} (the last one): {steps[current]}. All steps done."
        else:
            feedback_text = f"Completed step {current + 1}: {steps[current]}"
    else:
        next_index = current
        feedback_text = f"Not done yet: step {current + 1}: {steps[current]}"

    save_plan(
        latest["goal"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=next_index,
    )
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
