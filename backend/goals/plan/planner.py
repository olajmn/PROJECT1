"""
Planner
=======

Goal -> structured Plan, via a local LLM (Ollama). Produces a plan
across seven time horizons and revises it based on feedback, and owns
the decisions around creating a goal and reacting to feedback on one -
persisted via infrastructure/data_persistence.py's save_plan(), not
reimplemented here. Never talks to the model directly (see
model_client.py/step_generator.py).

Contents
1. Plan schema
2. Model prompts
3. Time helpers
4. Plan generation
5. Goal creation
6. Replanning
7. Feedback & step handling
8. CLI entry point

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

This file was goal_to_plan.py, then plan.py, then planner.py - "plan"
generates/orchestrates a plan, it doesn't define one, so the agent noun
fits its job better than the domain noun did. HORIZON_LABELS/
join_plan_prose() (presentation), ask_model() (model_client.py), and
generate_steps()/STEPS_SYSTEM_PROMPT (step_generator.py) have all since
moved to their own modules - none of them were Plan-orchestration
itself. PLAN_KEYS stayed - it's genuine Plan shape, passed INTO
ask_model() as a parameter rather than read by it directly, so the
split doesn't create a circular import. Full history:
docs/06-development.md, 2026-08-21/25.

Run from the PROJECT ROOT: .venv/bin/python -m backend.goals.plan.planner
"""

from datetime import datetime

from backend.foundation.time import (
    broadest_relevant_horizon,
    extract_duration_phrase,
    freeze_duration,
    resolve_duration,
    step_count,
)
from backend.goals.feedback.acknowledger import acknowledge
from backend.goals.feedback.feedback_parser import parse_outcome, requests_duration_change
from backend.goals.goal.resolver import get_history_for_goal
from backend.infrastructure.data_persistence import save_plan, save_vision
from backend.goals.plan.model_client import ask_model
from backend.goals.plan.step_generator import generate_steps

# ============================================================
# 1. Plan schema
# ============================================================

# Defined once. ask_model() validates the LLM's response has exactly
# these keys (passed in by generate_plan()/replan() below); the
# templates (via frontend/app.py) iterate this same list to render
# every horizon in order.
PLAN_KEYS = ("one_year", "one_month", "this_week", "today", "this_hour", "this_minute", "right_now")

# ============================================================
# 2. Model prompts
# ============================================================

SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time, and the user's goal. They may also tell you roughly "
    "how long they want this plan to span (e.g. '30 minutes', 'this "
    "week', '3 months'). Ground everything in the real date/time you "
    "were given - never invent specifics (names, numbers, progress) the "
    "user didn't tell you.\n\n"
    "First, decide whether the goal as given is specific enough to plan "
    "at all. A bare noun or verb with no object or context (e.g. "
    "'read', 'run', 'work', with nothing else said) isn't - answering it "
    "would mean inventing what book, what distance, what task, none of "
    "which the user actually told you. If so, do NOT invent an answer: "
    "set clarification to ONE short question that would make the goal "
    "specific enough to plan, and set every one of "
    "one_year/one_month/this_week/today/this_hour/this_minute/right_now "
    "to JSON null.\n\n"
    "Otherwise, set clarification to JSON null. The plan has seven "
    "horizons, from broadest to narrowest: one_year, one_month, "
    "this_week, today, this_hour, this_minute, right_now - but not "
    "every goal's real timeframe reaches all the way up to one_year. "
    "You will be told exactly which of these horizons to FILL IN and "
    "which to leave as JSON null, based on the goal's actual given "
    "timeframe - respect that list exactly. Do NOT invent a value for "
    "any horizon you were told to leave null, even a plausible-sounding "
    "one - a goal given '3 months' has no honest one_year answer, "
    "inventing one anyway is fabrication, not planning. For every "
    "horizon you WERE told to fill in, give a concrete, realistic "
    "value, framed as how this goal connects to or fits within that "
    "time window (e.g. a habit it's part of, a pattern it continues, "
    "what stays true a year on, what's realistic to finish today, "
    "within this one hour, within this one minute).\n"
    "- right_now is different from the horizons above it: not a time "
    "window description, but the actual trigger - the single most "
    "immediate, concrete action the user can take this very moment, "
    "small enough to start in the next 5 minutes. Always filled in, "
    "never one of the ones left null.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly these "
    "eight keys - clarification, one_year, one_month, this_week, today, "
    "this_hour, this_minute, right_now - each either a string value or "
    "JSON null as described above.\n"
)

REPLAN_SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time. The user already has a plan for their goal and is "
    "now giving you feedback on whether they completed the most "
    "immediate action ('right_now'). You will also see this goal's "
    "full history: every right_now action tried so far, oldest first, "
    "each with the feedback that followed it - not just the single "
    "most recent step. Adjust the plan based on the latest feedback:\n"
    "- If they did NOT complete it, look at the history first. If "
    "right_now has already been made smaller one or more times without "
    "being completed, do NOT shrink it again - repeatedly shrinking the "
    "same preparatory step is not real progress, and there is no value "
    "in an action smaller than a few minutes. Instead, either directly "
    "address a concrete obstacle they named, or move the action toward "
    "actually attempting the core thing the goal itself names (e.g. if "
    "the goal is 'send 4 applications' and right_now has only ever been "
    "research/browsing, the next right_now should be to actually send "
    "one application, even in the smallest real form - not more "
    "research). Only make right_now smaller the FIRST time it isn't "
    "completed, when the history shows no earlier shrink already "
    "happened.\n"
    "- If they DID complete it, move on to the next logical step.\n\n"
    "Ground everything in the real date/time you were given - never "
    "invent specifics (names, numbers, progress) the user didn't tell "
    "you.\n\n"
    "You will be told exactly which horizons should have a concrete "
    "value and which should be JSON null, same as the previous plan - "
    "this doesn't change on a replan just because the goal's scope "
    "grew in conversation. Never invent a value for a horizon named as "
    "null. Update whichever of the horizons you ARE filling in the "
    "feedback affects; carry the others forward unchanged if the "
    "feedback doesn't touch them.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly the "
    "same keys as before: one_year, one_month, this_week, today, "
    "this_hour, this_minute, right_now - each either a string value or "
    "JSON null.\n"
)


# ============================================================
# 3. Time helpers
# ============================================================


def _now_str() -> str:
    """
    Human-readable current local date and time, e.g. "Wednesday,
    2026-08-19 17:35". Passed to the model on every call so "right now"
    is grounded in the real current moment instead of the model having
    no sense of time at all.
    """
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M")


def _horizon_scope_instruction(duration: str | None) -> str:
    """
    The exact "fill these horizons in, leave these as null" line to
    append to a prompt's user_content - shared by generate_plan() and
    replan() so both ever compute the boundary the same one way (see
    frozen_duration.py §3 - Horizon scoping). Always names
    right_now as one to fill (it's never the broadest relevant horizon
    itself, but the loop below still includes it since it's always the
    last/narrowest PLAN_KEYS entry).
    """
    broadest = broadest_relevant_horizon(duration)
    start = PLAN_KEYS.index(broadest)
    fill_keys = PLAN_KEYS[start:]
    null_keys = PLAN_KEYS[:start]
    instruction = f"\n\nFill in these horizons: {', '.join(fill_keys)}."
    if null_keys:
        instruction += f" Leave these horizons as JSON null: {', '.join(null_keys)}."
    return instruction


def frozen_duration_for(plan: dict, duration: str | None) -> dict | None:
    """
    The frozen_duration to save alongside `plan` - None while `plan` is
    a clarification (nothing has actually started yet, so there's no
    honest countdown to freeze), otherwise freeze_duration(duration).
    Shared by generate_plan()'s and replan()'s callers (frontend/app.py)
    so this rule is expressed once instead of repeated at every call
    site that saves a plan.
    """
    return None if plan.get("clarification") else freeze_duration(duration)


# ============================================================
# 4. Plan generation
# ============================================================


def generate_plan(goal: str, duration: str | None = None) -> dict:
    """
    Takes a goal (a text string) and asks the local model to produce a
    structured plan, grounded in the real current date/time. `duration`
    is optional free text from the user (e.g. "30 minutes", "this
    week") describing how far ahead this plan should reach - no fixed
    choices, whatever the user types is passed straight through.
    Returns a dict with keys: clarification, one_year, one_month,
    this_week, right_now, steps.

    `clarification` (added 2026-08-21) is a single question (string)
    instead of a real plan when the goal as given is too vague to plan
    at all - e.g. a bare noun/verb like "read", with no object or
    context (see SYSTEM_PROMPT). Every other key is JSON null in that
    case; callers MUST check `clarification` first and, if it's set,
    treat this as "ask the user again", not as a plan to save - there's
    nothing real in the rest of the dict to act on yet.

    `steps` (added 2026-08-21) is a list of short step descriptions
    only when `duration` actually resolves to a real span (see
    frozen_duration.py §4 - Step planning) - None otherwise (no
    duration given, or free text that isn't grounded in a real span, or
    a clarification question came back instead of a plan). There's
    nothing honest to break into steps without a real timeframe to
    divide - same reasoning DEADLINE_RE's ungrounded deadlines already
    follow elsewhere in this project.

    Does NOT take a `vision_id`/Vision text yet (added 2026-08-26, see
    docs/03-architecture.md § Vision) - a goal's
    optional Vision is stored (data_persistence.save_plan()'s
    `vision_id`) but not yet supplied to the model here. If/when it is,
    this is the natural place: a caller would resolve `vision_id` to
    its text (data_persistence.get_vision()) and add one short line to
    `user_content` below, the same way `duration` is added - contextual
    framing for the model, never something Vision generates or decides
    on its own (see that doc section: "Vision -> contextualizes Goals",
    not "Vision -> generates every Goal").
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    plan = ask_model(SYSTEM_PROMPT, user_content, PLAN_KEYS + ("clarification",))

    plan["steps"] = None
    if plan.get("clarification"):
        return plan
    if duration:
        count = step_count(duration)
        if count is not None:
            plan["steps"] = generate_steps(goal, plan.get("right_now") or goal, count)
    return plan


# ============================================================
# 5. Goal creation
# ============================================================


def create_goal(typed_text: str, new_vision_text: str, vision_id_value: str) -> dict:
    """
    Handle the "set a goal" form: generate a fresh plan and save it.
    `typed_text`, `new_vision_text`, and `vision_id_value` are already
    read and stripped by the caller (frontend/app.py's new_goal()).

    One text field, not a separate goal/duration pair -
    `extract_duration_phrase()` (phrase_matching.py §5 - Public entry
    point) searches whatever was typed for a recognized time phrase
    anywhere inside it (e.g. "clean the apartment this weekend"), the
    same matchers a dedicated duration field would use, just applied
    to the whole sentence. If NOTHING recognized turns up at all,
    that's treated as "no timeframe given" DETERMINISTICALLY, before
    even calling the model - a fixed clarifying-question round is
    saved asking for one, same "code decides, model is just told"
    reasoning as the horizon-scope fix (see §3 - Time helpers,
    _horizon_scope_instruction()) rather than relying on the model to
    reliably notice this itself (see docs/05-decisions.md, 2026-08-23).

    Only ever starts a genuinely NEW goal - always requires typed text
    (enforced by the caller), and mints its own goal_id via
    save_plan(). Extending an EXISTING goal's timeframe is a
    conversational flow instead - see apply_feedback()'s
    requests_duration_change() branch (§7 - Feedback & step handling),
    which asks for and applies a new duration through the goal's own
    chat thread via apply_new_duration().

    Computes a FRESH `frozen_duration` (see
    backend/foundation/time/time_logic/frozen_duration.py's
    freeze_duration()) whenever a real plan comes back - EXCEPT when
    generate_plan() comes back with `clarification` set instead (see
    that function's docstring) - the goal as typed was too vague in
    CONTENT (a bare noun/verb, e.g. "read") to plan at all, a different
    case from missing TIME below. That round is saved too (as a new
    active goal entry) so the question shows up in the goal's own
    conversation thread and the user can answer it right there via the
    normal feedback box - see apply_feedback() below, which is what
    actually resolves a pending clarification into a real plan. But its
    `frozen_duration` is left None rather than frozen now: nothing has
    actually started yet while a question is still pending, so there's
    no honest countdown to draw until apply_feedback() resolves it into
    a real plan and freezes it then.

    `vision_id`/`new_vision` (added 2026-08-26): optional. A goal can
    be linked to an existing Vision (the `vision_id` select) or a
    freshly-typed one (`new_vision`, created here via save_vision() if
    non-empty - checked first, so typing a new one always wins over
    whatever the select happened to have selected). Neither is
    required - most goals have no vision at all, and that's the normal
    case, not a partial state. Set once, at creation, like `goal_id`
    itself; carried forward unchanged on every later replan for this
    goal (see apply_new_duration() and apply_feedback() below) - a
    goal's vision doesn't change just because its plan does.
    """
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
        return save_plan(typed_text, clarification_plan, duration=None, frozen_duration=None, vision_id=vision_id)
    plan = generate_plan(typed_text, duration)
    return save_plan(
        typed_text, plan, duration=duration,
        frozen_duration=frozen_duration_for(plan, duration),
        vision_id=vision_id,
    )


# ============================================================
# 6. Replanning
# ============================================================


def replan(goal: str, history: list[dict], feedback: str, duration: str | None = None) -> dict:
    """
    Takes the goal, the goal's full history so far (every record saved
    for it, oldest first - see storage.get_history_for_goal()), and the
    user's feedback on the most recent "right_now" action, then asks the
    model to produce an updated plan. `duration` is the same span
    originally given to generate_plan() (if any) - passed again here so
    the model keeps respecting it on every replan, not just the first
    call. Returns a dict with the same shape as generate_plan().

    Passing the *whole* history (not just the previous plan) is what
    lets REPLAN_SYSTEM_PROMPT's "don't shrink right_now more than once"
    rule actually work - a model only ever shown the single most recent
    step has no way to notice it has already made the same task smaller
    several times in a row. Without it, a goal's right_now can drift -
    e.g. from "research 4 companies" down to "check the news for 30
    seconds" over 13 replans (2026-08-20), never advancing toward the
    goal's actual action (sending an application) - see
    docs/06-development.md.

    Same Vision note as generate_plan() above: not supplied here either yet.
    """
    # Named history_lines, not "steps" - unrelated to this file's
    # `steps` plan field/step_generator.generate_steps() (added later
    # the same day); this is prose lines for the replan prompt, not
    # the step list.
    history_lines = []
    for record in history:
        right_now = record["plan"].get("right_now") or "(none)"
        if record.get("feedback"):
            history_lines.append(f'- right_now: "{right_now}" -> feedback: "{record["feedback"]}"')
        else:
            history_lines.append(f'- right_now: "{right_now}" (the first plan, no feedback yet)')
    history_text = "\n".join(history_lines)

    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My goal is: {goal}\n\n"
        f"This goal's full history so far, oldest first:\n{history_text}\n\n"
        f"My feedback on the most recent 'right_now' action: {feedback}"
    )
    if duration:
        user_content += f"\n\nThis plan should still span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    return ask_model(REPLAN_SYSTEM_PROMPT, user_content, PLAN_KEYS)


def apply_new_duration(existing: dict, duration: str, feedback: str) -> dict:
    """
    Regenerate `existing`'s plan around a new duration span - the
    shared logic behind /feedback's conversational
    requests_duration_change() flow (frontend/app.py; asking for and
    applying a new timeframe through the goal's own chat thread).

    Always calls generate_plan() again, never just patches
    duration/frozen_duration onto the existing record: changing the
    timeframe is a real new planning decision (new horizons filled, a
    new step list from step_generator.py's generate_steps()), not a
    countdown edit. frozen_duration_for() handles the case where the
    new duration turns out too vague in CONTENT to plan at all
    (generate_plan() comes back with `clarification` set) - nothing has
    actually started yet in that case, same reasoning /goal and
    /feedback's own clarification handling already follow.

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
        frozen_duration=frozen_duration_for(plan, duration),
        vision_id=existing.get("vision_id"),
    )


# ============================================================
# 7. Feedback & step handling
# ============================================================


def apply_feedback(latest: dict, note: str) -> dict:
    """
    Handle the "what's going on" form: classify the free-text note into
    an outcome (see feedback_parser.parse_outcome() - no LLM,
    recognized phrases only), then act on it exactly as the old
    Yes/Still working on it/No/Goal complete buttons used to. There's
    no separate "outcome" field anymore - the note itself is the only
    signal, so typing doesn't mean picking which of four boxes your
    situation best fits; see docs/05-decisions.md, 2026-08-20, for why
    this replaced the buttons and why it still never lets an LLM decide
    true/false.

    Before any of that, two earlier checks can take over the note
    entirely instead of treating it as a progress report:
    - `plan.clarification` set -> the note ANSWERS a pending question
      about the goal itself (see that branch below).
    - `plan.pending_duration_question` set -> the note answers "how
      long do you want this to run now?" (see apply_new_duration()).
    - otherwise, `requests_duration_change(note)` -> the note is a NEW
      request to change the timeframe (e.g. "can we change timeframe"),
      not a status report; applies immediately if a new duration is
      ALSO already in this same message (e.g. "change timeframe to 1
      hour"), otherwise asks the follow-up question and lets the
      pending_duration_question branch above catch the answer on the
      NEXT message. The goal's own conversation box is the only way to
      do this - there's no separate "extend timeframe" control on the
      card.

    `note` is already read and stripped by the caller (frontend/app.py's
    feedback()). Which goal this applies to is `latest` itself - the
    caller resolves it from the form's `goal_id` (each active goal's
    card posts its own), not "whatever was touched most recently
    overall". With more than one active goal shown at once, that
    distinction is the difference between feedback landing on the goal
    you actually meant versus a different one entirely.
    """
    duration = latest.get("duration")

    if latest["plan"].get("clarification"):
        # This goal has no real plan yet - the agent asked a clarifying
        # question instead (see generate_plan()'s docstring), and
        # `note` is the ANSWER to that question, not a status report on
        # a task that doesn't exist yet. Route it through generate_plan()
        # again (not replan(), which is built entirely around "did you
        # complete right_now" - there is no right_now here to have
        # completed), never through parse_outcome() below: an answer
        # like "speed and comprehension" isn't an
        # action_completed/action_not_completed/action_in_progress
        # signal at all, forcing it through that parser would be a
        # category error, not just an inaccurate guess.
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
        # long should it take?" question (see create_goal()'s
        # deterministic missing-timeframe check) - the answer to THAT
        # question is a duration phrase, not just more goal content, so
        # it needs the same extract_duration_phrase() extraction
        # create_goal()'s own new-goal path already does - otherwise a
        # real answer like "this week" stays lost as untyped prose
        # forever (2026-08-23: "Your answer" never produced a real plan
        # for exactly this class of clarification). Only attempted
        # while duration is still unknown - an already-known duration
        # (a content-vagueness clarification, e.g. "read") is left
        # alone, since `note` there answers a different question
        # entirely and isn't a timeframe to (mis)parse.
        if duration is None:
            duration = extract_duration_phrase(note)
        plan = generate_plan(combined_goal, duration)
        # frozen_duration stays None for as long as clarification keeps
        # coming back (same reasoning as create_goal() above: nothing
        # has actually started yet) - only frozen for real, for the
        # first time, the moment a real plan finally comes back.
        return save_plan(
            latest["goal"], plan, feedback=note, duration=duration,
            goal_id=latest["goal_id"],
            frozen_duration=frozen_duration_for(plan, duration),
            vision_id=latest.get("vision_id"),
        )

    if latest["plan"].get("pending_duration_question"):
        # The PREVIOUS record in this goal's thread asked "how long do
        # you want this to run now?" (see requests_duration_change()
        # below) - this note is the answer, a duration phrase, not a
        # status report on right_now. Falls back to the existing
        # duration unchanged if nothing recognized, same as the old
        # "Extend timeframe" form's own empty-submit behavior - never
        # silently wipes a working timeframe just because the answer
        # wasn't understood.
        new_duration = extract_duration_phrase(note) or duration
        return apply_new_duration(latest, new_duration, feedback=note)

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
            return apply_new_duration(latest, new_duration, feedback=note)

        # Carries the current plan/duration/steps forward completely
        # unchanged (this goal isn't being replanned or checked in on
        # right now) - only difference from a plain "carry forward"
        # save is the pending_duration_question flag, which is what
        # makes the branch above fire on the NEXT message and is what
        # active_goal/_conversation.html's thread shows as the agent's reply
        # instead of the real right_now.
        return save_plan(
            latest["goal"],
            {**latest["plan"], "pending_duration_question": "How long do you want this to run now?"},
            feedback=note, duration=duration, goal_id=latest["goal_id"],
            frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
            vision_id=latest.get("vision_id"),
        )

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # frozen_duration.py §1 (Freezing a duration) and
    # infrastructure/data_persistence.py's save_plan() docstring for
    # why re-deriving this from "now" here was the actual bug). Falls
    # back to computing one fresh only for a goal saved before
    # frozen_duration existed (2026-08-21) - a one-time "adopt now" so
    # it isn't permanently stuck without a bar, not a recurring
    # recompute.
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
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
            frozen_duration=frozen, vision_id=latest.get("vision_id"),
        )

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
        # honest about which one actually happened. The "couldn't tell"
        # case asks the model for a natural acknowledgment of `note`
        # (acknowledge() - display text only; it can never change this
        # branch or fail this route, see its own docstring).
        prefix = "Still working on it." if classified else acknowledge(note)
        feedback_text = prefix + (f" Note: {note}" if note else "")
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, goal_id=latest["goal_id"], frozen_duration=frozen,
            vision_id=latest.get("vision_id"),
        )

    outcome = "Completed the action" if outcome_value == "action_completed" else "Did not complete the action"
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    # The full chain, not just latest["plan"] - see replan()'s docstring
    # for why: a model only shown the single previous step has no way to
    # notice it has already shrunk right_now several times in a row.
    new_plan = replan(latest["goal"], get_history_for_goal(latest["goal_id"]), feedback_text, duration=duration)
    # goal_id carried forward explicitly - without this, save_plan() would
    # mint a fresh one and this replan would silently start a *new*
    # goal entry instead of continuing the existing goal's chain.
    return save_plan(
        latest["goal"], new_plan, feedback=feedback_text, duration=duration,
        goal_id=latest["goal_id"], frozen_duration=frozen, vision_id=latest.get("vision_id"),
    )


def advance_step(latest: dict, done: bool) -> dict:
    """
    Handle the per-step "Done?" Yes/No control (see
    frontend/templates/active_goal/_task.html) - advances `current_step` by
    one, purely by index arithmetic into the goal's already-generated
    `plan.steps` list. No model call at all: unlike apply_feedback()'s
    free-text note (which can trigger replan() - the model
    reconsidering the plan), the step list was already fully decided
    upfront (see step_generator.generate_steps()), so moving through it
    is just "which one are we on now", nothing to ask the model about.

    `done=False` doesn't move the pointer - it's logged the same safe,
    no-replan way apply_feedback()'s "in_progress" is, so a step can't
    be silently reworded/shrunk just because it wasn't done yet either.

    `current_step` can reach `len(steps)` (one past the last valid
    index, not a real step) to mean "every step is done" - see
    active_goal/_task.html for how that's shown (no more Yes/No, a
    prompt to mark the whole goal complete via the existing free-text
    box instead, not an automatic completion this function decides on
    its own).

    Returns `latest` unchanged if there's nothing to advance (no step
    list, or already at "all steps done"); otherwise the saved record.
    """
    steps = latest["plan"].get("steps")
    if not steps:
        # Nothing to advance - no step list on this goal at all (see
        # generate_plan(): only goals with a resolvable duration get one).
        return latest

    current = latest.get("current_step", 0)
    if current >= len(steps):
        # Already at "all steps done" - nothing left to confirm.
        return latest

    if done:
        next_index = current + 1
        if next_index >= len(steps):
            feedback_text = f"Completed step {current + 1} (the last one): {steps[current]}. All steps done."
        else:
            feedback_text = f"Completed step {current + 1}: {steps[current]}"
    else:
        next_index = current
        feedback_text = f"Not done yet: step {current + 1}: {steps[current]}"

    return save_plan(
        latest["goal"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=next_index,
        vision_id=latest.get("vision_id"),
    )


# ============================================================
# 8. CLI entry point
# ============================================================

# Only runs when this file is executed directly
# (not when other files import functions from it)
if __name__ == "__main__":
    my_goal = input("What do you want to achieve? ")
    print("\nThinking...\n")
    plan = generate_plan(my_goal)

    for horizon, text in plan.items():
        print(f"{horizon}: {text}")

    record = save_plan(my_goal, plan)
    print(f"\n[Saved as entry #{record['id']} in data/plans.json]")
