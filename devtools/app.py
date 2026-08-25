"""
Local interactive web interface for the agent.

This is a personal dev tool for talking to the agent through a browser
instead of running separate terminal scripts - NOT the product's real
frontend (see docs/03-architecture.md "Frontend direction").
Runs 100% locally, only reachable from this machine, no internet needed.

Run from the PROJECT ROOT (not from inside devtools/):
    .venv/bin/python -m devtools.app
The -m flag is required (not `python devtools/app.py`) so the
`from backend...` imports below can find the backend package. Lives as
a top-level sibling of backend/, not inside it (moved 2026-08-24) -
this talks TO the agent (the USER node in docs/03-architecture.md's
long-term diagram), it isn't part of the agent's own cognition, the
same category as tools/ and docs/, not backend/.
"""

from flask import Flask, redirect, render_template, request, url_for

from backend.foundation.time import (
    describe_duration,
    duration_progress,
    extract_duration_phrase,
    freeze_duration,
    step_plan,
)
from backend.goals.goal_logic.goal import get_board, get_history_for_goal, get_latest_for_goal
from backend.goals.goal_logic.outcome_classifier import classify_outcome, wants_duration_change
from backend.planning.plan import HORIZON_LABELS, PLAN_KEYS, generate_plan, join_plan_prose, replan
from backend.infrastructure.data_persistence import load_history, save_plan

# Custom folder names (2026-08-23, defaults were templates/ and
# static/) - explicit split of "frontend" (html/ - every .html file,
# nothing else) from CSS (css/) within this devtools app. Flask's
# `static` endpoint name and the url_for('static', ...) calls in the
# templates don't change just because the on-disk folder does - only
# WHERE Flask looks, not what anything is called from outside.
app = Flask(__name__, template_folder="html", static_folder="css")
# Makes describe_duration() callable directly from templates, e.g.
# {{ describe_duration(record.duration) }} in _plan_entry.html/index.html -
# so the "how was this understood" text stays in one place
# (backend/foundation/time/logic/duration_resolution.py) instead of being duplicated as static strings
# in the templates.
app.jinja_env.globals["describe_duration"] = describe_duration
# Same reasoning, for the start/now/end progress bar in
# active_goal/_timeperiod.html - percent/status/labels computed once in
# foundation/time/ (see duration_progress()'s docstring), not recomputed
# in template logic.
app.jinja_env.globals["duration_progress"] = duration_progress
# Same reasoning - the vertical step list in active_goal/_task.html and
# active_goal/_steps.html zips a goal's stored step descriptions
# (record.plan.steps, from backend/planning/plan.py's _generate_steps()) with
# their deterministically-computed time slice via step_plan() - see
# its docstring.
app.jinja_env.globals["step_plan"] = step_plan
# Same reasoning: lets active_goal/_conversation.html pull a goal's whole
# conversation (see get_history_for_goal's docstring) without every
# route that renders it having to fetch and pass that separately.
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal
# Same reasoning - joins Plan's filled-horizon sentences into one
# flowing paragraph (see active_goal/_plan.html, 2026-08-23) rather than a
# bare space-join done in the template itself.
app.jinja_env.globals["join_plan_prose"] = join_plan_prose

# The broader horizons shown alongside "right_now", on both the index
# page and the history page, in order, excluding "right_now" itself
# (which always gets its own highlighted box instead of being listed
# alongside the others). A goal with a short duration will have these
# come back as null/None - the templates skip any horizon that's falsy,
# so only the levels actually relevant to the goal show up.
_BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]


def split_message_lines(text: str) -> list[str]:
    """
    Split one chat message into its separate sentence-like parts, for
    active_goal/_conversation.html's thread to render each on
    its own line - a message built from more than one thought (e.g.
    app.py's own "Checked in (couldn't tell what this means yet). Note:
    {note}") otherwise reads as one dense run-on block instead of the
    distinct statements it actually is. Purely a DISPLAY concern (how
    devtools renders a string), not a data concern - the stored
    `feedback`/`right_now`/etc. text itself is untouched, still one
    plain string everywhere else (goal_log/history.html, _plan_entry.html, the
    JSON file itself).

    The exact reverse of backend/planning/plan.py's join_plan_prose() (". ".join
    of several texts): splits back on that same separator. A plain
    ". ".split() would silently swallow the period from every part
    except the last (join_plan_prose's job was gluing them INTO one
    string, so the separator eats it) - re-added here to each part that
    doesn't already end in its own sentence-ending punctuation, so a
    part like "Checked in (couldn't tell what this means yet)" reads as
    a complete sentence again once it's back on its own line.
    """
    if not text:
        return []
    parts = [p for p in text.split(". ") if p]
    return [
        p if i == len(parts) - 1 or p.rstrip().endswith((".", "!", "?", ":")) else p.rstrip() + "."
        for i, p in enumerate(parts)
    ]


# Registered as a filter (`{{ text | split_message_lines }}`), not a
# global like join_plan_prose/step_plan/etc. above - this transforms a
# string that's already in template scope (msg.feedback, msg.right_now,
# ...) rather than pulling in data the template doesn't have yet, so
# filter syntax reads more naturally at every call site.
app.jinja_env.filters["split_message_lines"] = split_message_lines


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
    (backend/foundation/time/logic/phrase_matching.py) searches whatever was typed for a
    recognized time phrase anywhere inside it (e.g. "clean the
    apartment this weekend"), the same matchers a dedicated duration
    field already used, just applied to the whole sentence instead of
    a field reserved for only that. If NOTHING recognized turns up at
    all, that's treated as "no timeframe given" DETERMINISTICALLY,
    before even calling the model - a fixed clarifying-question round
    is saved asking for one, same "code decides, model is just told"
    reasoning as the horizon-scope fix (see plan.py's
    _horizon_scope_instruction()) rather than relying on the model to
    reliably notice this itself (see docs/05-decisions.md, 2026-08-23,
    for why the model isn't trusted with judgment calls like this one
    when code can decide them outright).

    Only ever starts a genuinely NEW goal now (2026-08-23) - always
    requires typed text, and mints its own goal_id via save_plan().
    Extending an EXISTING goal's timeframe used to also go through here
    (`continue_goal_id`, posted by a standalone "Extend timeframe" form
    on that goal's own board card), but that's now done conversationally
    instead - see /feedback's `wants_duration_change()` branch below,
    which asks for and applies a new duration through the goal's own
    chat thread. `_apply_new_duration()` is the shared piece of logic
    that survived that move.

    Computes a FRESH `frozen_duration` (see backend/foundation/time/logic/frozen_duration.py's
    freeze_duration()) whenever a real plan comes back - EXCEPT when
    `generate_plan()` comes back with `clarification` set instead (see
    that function's docstring) - the goal as typed was too vague in
    CONTENT (a bare noun/verb, e.g. "read") to plan at all, a different
    case from missing TIME below. That round is saved too (as a new
    active board entry) so the question shows up in the goal's own
    conversation thread and the user can answer it right there via the
    normal feedback box - see /feedback below, which is what actually
    resolves a pending clarification into a real plan. But its
    `frozen_duration` is left None rather than frozen now: nothing has
    actually started yet while a question is still pending, so there's
    no honest countdown to draw until /feedback resolves it into a real
    plan and freezes it then. Redirects straight to the card either way
    (`#goal-{id}`, same anchor /feedback uses) so the question is
    immediately visible, not buried below the fold.
    """
    typed_text = request.form.get("goal", "").strip()

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


def _apply_new_duration(existing: dict, duration: str, feedback: str) -> dict:
    """
    Regenerate `existing`'s plan around a new duration span - the piece
    of logic that survived /goal's old `continue_goal_id` branch (moved
    here 2026-08-23 when that branch's only caller, the standalone
    "Extend timeframe" form, was replaced by /feedback's conversational
    wants_duration_change() flow below).

    Always calls generate_plan() again, never just patches
    duration/frozen_duration onto the existing record: changing the
    timeframe is a real new planning decision (new horizons filled, a
    new step list from backend/planning/plan.py's _generate_steps()), not a
    countdown edit - same as it always was here, just triggered by a
    chat message now instead of a form submit. frozen_duration stays
    None if the new duration turns out too vague in CONTENT to plan at
    all (generate_plan() comes back with `clarification` set) - nothing
    has actually started yet in that case, same reasoning /goal and
    /feedback's own clarification handling already follow.

    `feedback` is the user's own raw typed note (e.g. "5 months", or
    "can we change timeframe to 1 hour") - stored as-is, same as every
    other /feedback branch does with `note`, so it shows up as the
    "You" message in the conversation thread. Missing until 2026-08-23:
    this call never passed it at all, so the record got feedback=None -
    not a rendering bug, an actual empty bubble in the saved history
    (the "You" reply to "How long do you want this to run now?" showed
    the label with no text under it).
    """
    plan = generate_plan(existing["goal"], duration)
    return save_plan(
        existing["goal"], plan, feedback=feedback, duration=duration, goal_id=existing["goal_id"],
        frozen_duration=None if plan.get("clarification") else freeze_duration(duration),
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle the "what's going on" form: classify the free-text note into
    an outcome (see backend/goals/goal_logic/outcome_classifier.py - no LLM, recognized
    phrases only), then act on it exactly as the old Yes/Still working
    on it/No/Goal complete buttons used to. There's no separate
    "outcome" field anymore - the note itself is the only signal, so
    typing doesn't mean picking which of four boxes your situation
    best fits; see docs/05-decisions.md, 2026-08-20, for why this
    replaced the buttons and why it still never lets an LLM decide
    true/false.

    Before any of that, two earlier checks can take over the note
    entirely instead of treating it as a progress report:
    - `plan.clarification` set -> the note ANSWERS a pending question
      about the goal itself (see that branch below).
    - `plan.pending_duration_question` set -> the note answers "how
      long do you want this to run now?" (see _apply_new_duration()).
    - otherwise, `wants_duration_change(note)` -> the note is a NEW
      request to change the timeframe (e.g. "can we change timeframe"),
      not a status report; applies immediately if a new duration is
      ALSO already in this same message (e.g. "change timeframe to 1
      hour"), otherwise asks the follow-up question and lets the
      pending_duration_question branch above catch the answer on the
      NEXT message. Replaces the old standalone "Extend timeframe"
      form (2026-08-23) - the goal's own conversation box is now the
      only way to do this, no separate control on the card.

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
    # registered below however much history came before it (2026-08-20,
    # see docs/06-development.md): without it, repeated "Still working
    # on it" clicks look broken for exactly this reason - the save
    # always worked, the confirmation was just scrolled out of view.
    back_to = redirect(url_for("index") + f"#goal-{latest['goal_id']}")

    if latest["plan"].get("clarification"):
        # This goal has no real plan yet - the agent asked a clarifying
        # question instead (see backend/planning/plan.py's generate_plan()
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
        # `duration` can still be None here specifically when this
        # clarification IS the "When do you want to do this, or how
        # long should it take?" question (see /goal's deterministic
        # missing-timeframe check) - the answer to THAT question is a
        # duration phrase, not just more goal content, so it needs the
        # same extract_duration_phrase() extraction /goal's own
        # new-goal path already does - otherwise a real answer like
        # "this week" stays lost as untyped prose forever (2026-08-23:
        # "Your answer" never produced a real plan for exactly this
        # class of clarification). Only attempted
        # while duration is still unknown - an already-known duration
        # (a content-vagueness clarification, e.g. "read") is left
        # alone, since `note` there answers a different question
        # entirely and isn't a timeframe to (mis)parse.
        if duration is None:
            duration = extract_duration_phrase(note)
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

    if latest["plan"].get("pending_duration_question"):
        # The PREVIOUS record in this goal's thread asked "how long do
        # you want this to run now?" (see wants_duration_change() below)
        # - this note is the answer, a duration phrase, not a status
        # report on right_now. Falls back to the existing duration
        # unchanged if nothing recognized, same as the old "Extend
        # timeframe" form's own empty-submit behavior - never silently
        # wipes a working timeframe just because the answer wasn't
        # understood.
        new_duration = extract_duration_phrase(note) or duration
        _apply_new_duration(latest, new_duration, feedback=note)
        return back_to

    if wants_duration_change(note):
        # A request to change the TIMEFRAME, not a progress report -
        # checked before classify_outcome() so it can never be
        # misread as one of its four outcomes (see
        # outcome_classifier.wants_duration_change()'s docstring for
        # why this can't just be a fifth RULES entry).
        #
        # The new duration might already be IN this same message (e.g.
        # "can we change timeframe to 1 hour") - checked first so that
        # case applies it immediately instead of asking a question
        # you've already answered - the first version (2026-08-23)
        # always asked "how long...?" even when the answer was right
        # there, silently discarding it. Only asks
        # the follow-up when nothing recognized turns up.
        new_duration = extract_duration_phrase(note)
        if new_duration:
            _apply_new_duration(latest, new_duration, feedback=note)
            return back_to

        # Carries the current plan/duration/steps forward completely
        # unchanged (this goal isn't being replanned or checked in on
        # right now) - only difference from a plain "carry forward"
        # save is the pending_duration_question flag, which is what
        # makes the branch above fire on the NEXT message and is what
        # active_goal/_conversation.html's thread shows as the agent's reply
        # instead of the real right_now.
        save_plan(
            latest["goal"],
            {**latest["plan"], "pending_duration_question": "How long do you want this to run now?"},
            feedback=note, duration=duration, goal_id=latest["goal_id"],
            frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        )
        return back_to

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # backend/foundation/time/logic/frozen_duration.py's freeze_duration() and
    # backend/infrastructure/data_persistence.py's save_plan() docstring for why re-deriving
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
        # "No" (see docs/06-development.md, 2026-08-20): three rapid
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
    Handle the per-step "Done?" Yes/No control (see active_goal/_task.html) -
    advances `current_step` by one, purely by index arithmetic into the
    goal's already-generated `plan.steps` list. No model call at all:
    unlike /feedback's free-text note (which can trigger replan() -
    the model reconsidering the plan), the step list was already fully
    decided upfront (see backend/planning/plan.py's _generate_steps()), so
    moving through it is just "which one are we on now", nothing to
    ask the model about.

    "No" doesn't move the pointer - it's logged the same safe,
    no-replan way /feedback's "in_progress" is, so a step can't be
    silently reworded/shrunk just because it wasn't done yet either.

    `current_step` can reach `len(steps)` (one past the last valid
    index, not a real step) to mean "every step is done" - see
    active_goal/_task.html for how that's shown (no more Yes/No, a prompt to
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
        # backend/planning/plan.py's generate_plan(): only goals with a
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
    return render_template("goal_log/history.html", history=load_history(), horizons=_BROADER_HORIZONS)


@app.route("/completed")
def completed():
    """
    Completed goals only, on their own page (2026-08-23; used to be
    /board, showing Active alongside Completed) - index.html already
    shows Active, so a second page repeating it never earned its keep.
    get_board() still computes both halves (it groups ALL history by
    goal_id, splitting into active/completed is just what falls out of
    that in one pass - see backend/goals/goal_logic/goal.py) but only `board.completed`
    is ever read here now, via completed_goal/_completed.html.
    """
    return render_template("completed_goal/completed.html", board=get_board(), horizons=_BROADER_HORIZONS)


if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
