"""
Devtools App
============

Local interactive web interface for the agent - a personal dev tool
for talking to the agent through a browser instead of running separate
terminal scripts. NOT the product's real frontend (see
docs/03-architecture.md "Frontend direction"). Runs 100% locally, only
reachable from this machine, no internet needed.

Contents
1. Setup
2. Board building
3. Routes - board & vision
4. Routes - goal creation & duration changes
5. Routes - feedback & step tracking
6. Routes - history views
7. CLI entry point

Run from the PROJECT ROOT (not from inside devtools/):
    .venv/bin/python -m devtools.app
The -m flag is required (not `python devtools/app.py`) so the
`from backend...` imports below can find the backend package. Lives as
a top-level sibling of backend/ (this talks TO the agent, it isn't
part of the agent's own cognition - the same category as tools/ and
docs/, not backend/); full history: docs/06-development.md, 2026-08-24.
"""

from flask import Flask, redirect, render_template, request, url_for

from backend.foundation.time import (
    describe_duration,
    duration_progress,
    extract_duration_phrase,
    freeze_duration,
    step_plan,
)
from backend.goals.goal_logic.resolver import (
    created_at_key,
    get_history_for_goal,
    get_latest_for_all_goals,
    get_latest_for_goal,
)
from backend.goals.goal_logic.feedback_parser import parse_outcome, requests_duration_change
from backend.planning.planner import PLAN_KEYS, generate_plan, replan
from backend.infrastructure.data_persistence import load_history, load_visions, save_plan, save_vision

# ============================================================
# 1. Setup
# ============================================================

# Custom folder names (defaults were templates/ and static/) - explicit
# split of "frontend" (html/ - every .html file,
# nothing else) from CSS (css/) within this devtools app. Flask's
# `static` endpoint name and the url_for('static', ...) calls in the
# templates don't change just because the on-disk folder does - only
# WHERE Flask looks, not what anything is called from outside.
app = Flask(__name__, template_folder="html", static_folder="css")
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
# (record.plan.steps, from backend/planning/step_generator.py's generate_steps()) with
# their deterministically-computed time slice via step_plan() - see
# its docstring.
app.jinja_env.globals["step_plan"] = step_plan
# Same reasoning: lets active_goal/_conversation.html pull a goal's whole
# conversation (see get_history_for_goal's docstring) without every
# route that renders it having to fetch and pass that separately.
app.jinja_env.globals["get_history_for_goal"] = get_history_for_goal

# ============================================================
# 2. Board building
# ============================================================

# A display label per PLAN_KEYS entry - not part of the Plan's shape
# (planner.PLAN_KEYS is that), just how each horizon is worded here.
# Lives here, not in planner.py, alongside join_plan_prose() below -
# both are presentation-only, never read by Plan's own logic.
HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "today": "Today",
    "this_hour": "This hour",
    "this_minute": "This minute",
    "right_now": "Right now",
}

# The broader horizons shown alongside "right_now", on both the index
# page and the history page, in order, excluding "right_now" itself
# (which always gets its own highlighted box instead of being listed
# alongside the others). A goal with a short duration will have these
# come back as null/None - the templates skip any horizon that's falsy,
# so only the levels actually relevant to the goal show up.
_BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]


def join_plan_prose(texts: list[str]) -> str:
    """
    Join a plan's filled-horizon sentences into one flowing paragraph
    (see devtools/html/active_goal/_plan.html). Strips each piece's own
    trailing punctuation/whitespace before re-joining with ". " and a
    final period, rather than a bare space - the model doesn't
    consistently end a horizon's text with a period itself, so a plain
    space-join produces run-on-looking text with no visible sentence
    boundary (e.g. "...long-term Develop a meal planning system...").
    Empty string for an empty list - nothing to join, same as the
    template's own empty check.

    A DISPLAY concern (how devtools renders a plan), not Plan-domain
    logic - lives here, not in planner.py; see split_message_lines()
    below, its exact reverse.
    """
    cleaned = [text.strip().rstrip(".") for text in texts if text]
    if not cleaned:
        return ""
    return ". ".join(cleaned) + "."


# Same reasoning as split_message_lines below - joins Plan's
# filled-horizon sentences into one flowing paragraph (see
# active_goal/_plan.html) rather than a bare space-join done in the
# template itself.
app.jinja_env.globals["join_plan_prose"] = join_plan_prose


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

    The exact reverse of join_plan_prose() above (". ".join
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


def _group_active_by_vision(active_records: list[dict], visions: list[dict]) -> list[tuple[dict | None, list[dict]]]:
    """
    Group active board records by vision_id, for index.html - goals
    sharing a Vision render together under its heading; goals with no
    vision_id (the normal case) render in their own group, unheaded,
    last. Returns a list of (vision_record_or_None, [records]) pairs,
    vision groups oldest-vision-first, the no-vision group always last
    regardless of where it would otherwise fall.

    Presentation-only grouping for this one page, not a general Goal/
    Vision capability - deliberately kept here rather than added to
    goal_logic/resolver.py (which only resolves goal_id identity, not
    board shape - see _build_board() below - and is unchanged by
    Vision existing at all).
    """
    visions_by_id = {v["id"]: v for v in visions}
    groups: dict[int | None, list[dict]] = {}
    for record in active_records:
        groups.setdefault(record.get("vision_id"), []).append(record)

    with_vision = sorted(
        ((visions_by_id[vid], records) for vid, records in groups.items() if vid in visions_by_id),
        key=lambda pair: pair[0]["id"],
    )
    without_vision = groups.get(None, [])
    return with_vision + ([(None, without_vision)] if without_vision else [])


def _build_board() -> dict:
    """
    Split every goal's latest record into "active" and "completed",
    for the board views (index.html, completed_goal/_completed.html).
    Board-only shaping - see get_latest_for_all_goals()'s docstring
    for why this doesn't live in goal_logic/resolver.py.

    Returns {"active": [...], "completed": [...]}. "active" is newest
    first; "completed" stays in the order it always has (oldest-first,
    by when each goal_id first appeared in history).
    """
    latest = get_latest_for_all_goals()
    # .get(), not [] - records saved before the "completed" field
    # existed don't have the key at all.
    active = [r for r in latest if not r.get("completed")]
    completed = [r for r in latest if r.get("completed")]
    active.sort(key=created_at_key, reverse=True)
    return {"active": active, "completed": completed}


# ============================================================
# 3. Routes - board & vision
# ============================================================


@app.route("/")
def index():
    board = _build_board()
    visions = load_visions()
    return render_template(
        "index.html",
        horizons=_BROADER_HORIZONS,
        history=load_history(),
        board=board,
        visions=visions,
        vision_groups=_group_active_by_vision(board["active"], visions),
    )


@app.route("/vision", methods=["POST"])
def new_vision():
    """
    Handle the "set a vision" form: save a new Vision and return to the
    board. Create-only - see save_vision()'s docstring for why editing/
    deleting an existing one isn't built yet.

    Deliberately does not attach itself to any goal - a Vision exists
    independently first (see docs/03-architecture.md § Long-term
    architecture: it "provides optional context to multiple Goals", it
    isn't itself the first step of a pipeline). Attaching one to a goal
    happens in /goal's own form instead, via `vision_id`/`new_vision`.
    """
    text = request.form.get("text", "").strip()
    if text:
        save_vision(text)
    return redirect(url_for("index"))


# ============================================================
# 4. Routes - goal creation & duration changes
# ============================================================


@app.route("/goal", methods=["POST"])
def new_goal():
    """
    Handle the "set a goal" form: generate a fresh plan and save it.

    One text field, not a separate goal/duration pair -
    `extract_duration_phrase()` (phrase_matching.py §5 - Public entry
    point) searches whatever was typed for a recognized time phrase
    anywhere inside it (e.g. "clean the apartment this weekend"), the
    same matchers a dedicated duration field would use, just applied
    to the whole sentence. If NOTHING recognized turns up at all,
    that's treated as "no timeframe given" DETERMINISTICALLY, before
    even calling the model - a fixed clarifying-question round is
    saved asking for one, same "code decides, model is just told"
    reasoning as the horizon-scope fix (see planner.py §3 - Time
    helpers, _horizon_scope_instruction()) rather than relying on the
    model to reliably notice this itself (see docs/05-decisions.md,
    2026-08-23).

    Only ever starts a genuinely NEW goal - always requires typed text,
    and mints its own goal_id via save_plan(). Extending an EXISTING
    goal's timeframe is a conversational flow instead - see
    /feedback's `requests_duration_change()` branch below, which asks
    for and applies a new duration through the goal's own chat thread
    via `_apply_new_duration()`.

    Computes a FRESH `frozen_duration` (see backend/foundation/time/time_logic/frozen_duration.py's
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

    `vision_id`/`new_vision` (added 2026-08-26): optional. A goal can
    be linked to an existing Vision (the `vision_id` select) or a
    freshly-typed one (`new_vision`, created here via save_vision() if
    non-empty - checked first, so typing a new one always wins over
    whatever the select happened to have selected). Neither is
    required - most goals have no vision at all, and that's the normal
    case, not a partial state. Set once, at creation, like `goal_id`
    itself; carried forward unchanged on every later replan for this
    goal (see _apply_new_duration() and /feedback below) - a goal's
    vision doesn't change just because its plan does.
    """
    typed_text = request.form.get("goal", "").strip()

    if typed_text:
        new_vision_text = request.form.get("new_vision", "").strip()
        vision_id_value = request.form.get("vision_id", "").strip()
        if new_vision_text:
            vision_id = save_vision(new_vision_text)["id"]
        elif vision_id_value:
            vision_id = int(vision_id_value)
        else:
            vision_id = None

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
            record = save_plan(typed_text, clarification_plan, duration=None, frozen_duration=None, vision_id=vision_id)
            return redirect(url_for("index") + f"#goal-{record['goal_id']}")
        plan = generate_plan(typed_text, duration)
        record = save_plan(
            typed_text, plan, duration=duration,
            frozen_duration=None if plan.get("clarification") else freeze_duration(duration),
            vision_id=vision_id,
        )
        return redirect(url_for("index") + f"#goal-{record['goal_id']}")
    return redirect(url_for("index"))


def _apply_new_duration(existing: dict, duration: str, feedback: str) -> dict:
    """
    Regenerate `existing`'s plan around a new duration span - the
    shared logic behind /feedback's conversational
    requests_duration_change() flow below (asking for and applying a
    new timeframe through the goal's own chat thread).

    Always calls generate_plan() again, never just patches
    duration/frozen_duration onto the existing record: changing the
    timeframe is a real new planning decision (new horizons filled, a
    new step list from backend/planning/step_generator.py's generate_steps()), not a
    countdown edit. frozen_duration stays None if the new duration
    turns out too vague in CONTENT to plan at all (generate_plan()
    comes back with `clarification` set) - nothing has actually
    started yet in that case, same reasoning /goal and /feedback's own
    clarification handling already follow.

    `feedback` is the user's own raw typed note (e.g. "5 months", or
    "can we change timeframe to 1 hour") - stored as-is, same as every
    other /feedback branch does with `note`, so it shows up as the
    "You" message in the conversation thread.

    `existing["vision_id"]` is carried forward unchanged, same as
    `goal_id` - a changed duration is still the same goal continuing,
    not a new decision about which Vision it belongs to.
    """
    plan = generate_plan(existing["goal"], duration)
    return save_plan(
        existing["goal"], plan, feedback=feedback, duration=duration, goal_id=existing["goal_id"],
        frozen_duration=None if plan.get("clarification") else freeze_duration(duration),
        vision_id=existing.get("vision_id"),
    )


# ============================================================
# 5. Routes - feedback & step tracking
# ============================================================


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle the "what's going on" form: classify the free-text note into
    an outcome (see backend/goals/goal_logic/feedback_parser.py - no LLM, recognized
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
    - otherwise, `requests_duration_change(note)` -> the note is a NEW
      request to change the timeframe (e.g. "can we change timeframe"),
      not a status report; applies immediately if a new duration is
      ALSO already in this same message (e.g. "change timeframe to 1
      hour"), otherwise asks the follow-up question and lets the
      pending_duration_question branch above catch the answer on the
      NEXT message. The goal's own conversation box is the only way to
      do this - there's no separate "extend timeframe" control on the
      card.

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
        # question instead (see backend/planning/planner.py's generate_plan()
        # docstring), and `note` is the ANSWER to that question, not a
        # status report on a task that doesn't exist yet. Route it
        # through generate_plan() again (not replan(), which is built
        # entirely around "did you complete right_now" - there is no
        # right_now here to have completed), never through
        # parse_outcome() below: an answer like "speed and
        # comprehension" isn't an action_completed/action_not_completed/
        # action_in_progress signal at all, forcing it through that
        # parser would be a category error, not just an inaccurate guess.
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
            vision_id=latest.get("vision_id"),
        )
        return back_to

    if latest["plan"].get("pending_duration_question"):
        # The PREVIOUS record in this goal's thread asked "how long do
        # you want this to run now?" (see requests_duration_change() below)
        # - this note is the answer, a duration phrase, not a status
        # report on right_now. Falls back to the existing duration
        # unchanged if nothing recognized, same as the old "Extend
        # timeframe" form's own empty-submit behavior - never silently
        # wipes a working timeframe just because the answer wasn't
        # understood.
        new_duration = extract_duration_phrase(note) or duration
        _apply_new_duration(latest, new_duration, feedback=note)
        return back_to

    if requests_duration_change(note):
        # A request to change the TIMEFRAME, not a progress report -
        # checked before parse_outcome() so it can never be
        # misread as one of its four outcomes (see
        # feedback_parser.requests_duration_change()'s docstring for why
        # this can't just be another branch in parse_outcome()).
        #
        # The new duration might already be IN this same message (e.g.
        # "can we change timeframe to 1 hour") - checked first so that
        # case applies it immediately instead of asking a question
        # already answered in the same breath. Only asks the follow-up
        # when nothing recognized turns up.
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
            vision_id=latest.get("vision_id"),
        )
        return back_to

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # frozen_duration.py §1 (Freezing a duration) and
    # backend/infrastructure/data_persistence.py's save_plan() docstring for why re-deriving
    # this from "now" here was the actual bug). Falls back to computing
    # one fresh only for a goal saved before frozen_duration existed
    # (2026-08-21) - a one-time "adopt now" so it isn't permanently
    # stuck without a bar, not a recurring recompute.
    frozen = latest.get("frozen_duration") or freeze_duration(duration)
    classified = parse_outcome(note)
    # Anything not confidently recognized defaults to the same safe
    # no-op as "action_in_progress" - check in without changing the
    # plan, rather than guess toward a riskier outcome
    # (action_completed/goal_completed) from ambiguous text. See
    # parse_outcome()'s docstring.
    outcome_value = classified or "action_in_progress"

    if outcome_value == "goal_completed":
        # The whole goal is done, not just this one "right_now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
            frozen_duration=frozen, vision_id=latest.get("vision_id"),
        )
        return back_to

    if outcome_value == "action_in_progress":
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
            vision_id=latest.get("vision_id"),
        )
        return back_to

    outcome = "Completed the action" if outcome_value == "action_completed" else "Did not complete the action"
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
        goal_id=latest["goal_id"], frozen_duration=frozen, vision_id=latest.get("vision_id"),
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
    decided upfront (see backend/planning/step_generator.py's generate_steps()), so
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
        # backend/planning/planner.py's generate_plan(): only goals with a
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
        vision_id=latest.get("vision_id"),
    )
    return back_to


# ============================================================
# 6. Routes - history views
# ============================================================


@app.route("/history")
def history():
    return render_template("goal_log/history.html", history=load_history(), horizons=_BROADER_HORIZONS)


@app.route("/completed")
def completed():
    """
    Completed goals only, on their own page - index.html already shows
    Active, so a second page repeating it never earned its keep.
    _build_board() still computes both halves (it groups ALL history
    by goal_id, splitting into active/completed is just what falls out
    of that in one pass) but only `board.completed` is ever read here
    now, via completed_goal/_completed.html.
    """
    return render_template("completed_goal/completed.html", board=_build_board(), horizons=_BROADER_HORIZONS)


# ============================================================
# 7. CLI entry point
# ============================================================

if __name__ == "__main__":
    # Port 5050, not 5000: on modern macOS, port 5000 is often already
    # taken by the AirPlay Receiver system service - a common gotcha.
    app.run(host="127.0.0.1", port=5050, debug=True)
