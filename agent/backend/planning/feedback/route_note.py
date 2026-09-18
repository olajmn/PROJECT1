"""
Act on a free-text note against one existing goal record.

Parsing the note (feedback_parser.py) is a separate job from this:
that module names a signal, this one decides what to do with it -
including the earlier checks that take over before parse_outcome()
runs (a pending clarification, a pending suggestion, a duration
change). Those checks live here because they need the record's flags,
not because they are a second parser.

Calls into plan/planner.py for anything that actually produces or
revises a plan (generate_plan, replan, apply_new_duration). This
module does not talk to the model about planning; acknowledge() is
display text only, for notes parse_outcome() could not classify.

Nothing here is a Goal identity lookup - the caller already resolved
`latest`. See resolver.py for that.
"""

# Contents
#  1. Suggestion acceptance
#      - _SUGGESTION_ACCEPT_PHRASES
#      - _accepts_suggestion()
#
#  2. Routing a note
#      - route_note()

import re

from backend.foundation.time import extract_duration_phrase, freeze_duration
from backend.infrastructure.data_persistence import save_plan
from backend.planning.feedback.acknowledger import acknowledge
from backend.planning.feedback.feedback_parser import parse_outcome, requests_duration_change
from backend.planning.goal.resolver import get_history_for_goal
from backend.planning.plan import planner


# ============================================================
# 1. Suggestion acceptance
# ============================================================

# Deliberately separate from feedback_parser.ACTION_COMPLETED_PHRASES,
# and deliberately narrower: that list also recognizes "done"/"already
# did"/"finished"/etc. as completion, which are exactly wrong here - a
# still-undone suggested_action being accepted ("yes, let's do that")
# is not the same claim as an Action being reported done ("yes, I did
# it"), even though both can start with "yes" (see docs/planning-
# model.md's ASK vs. SUGGEST for why these differ). Only ever consulted
# while a `suggested_action` is actually pending (see route_note()),
# so there is no risk of this list ever reinterpreting an ordinary
# completion report.
_SUGGESTION_ACCEPT_PHRASES = ("yes", "yeah", "yep", "yup", "sure", "ok", "okay")


def _accepts_suggestion(note: str) -> bool:
    """
    True if `note` reads as accepting a pending `suggested_action` -
    same whole-word matching as feedback_parser._contains_phrase(), not
    imported from there since it's a private helper of that module and
    the phrase list itself is intentionally different (see above). An
    unrecognized reply is NOT guessed as acceptance - it falls through
    to route_note()'s re-evaluation branch instead, same "recognize
    what you can name, admit what you can't" discipline as
    feedback_parser.py.
    """
    normalized = note.strip().lower()
    return any(re.search(r"\b" + re.escape(phrase) + r"\b", normalized) is not None for phrase in _SUGGESTION_ACCEPT_PHRASES)


# ============================================================
# 2. Routing a note
# ============================================================


def route_note(latest: dict, note: str) -> dict:
    """
    Classify the free-text note into an outcome (parse_outcome() - no
    LLM, recognized phrases only) and act on it. The note itself is the
    only signal - no separate "outcome" field (see docs/05-decisions.md,
    2026-08-20, for why, and why this never lets an LLM decide true/false).

    Before that, several earlier checks can take over the note entirely
    instead of treating it as a progress report:
    - `plan.clarification` set -> the note ANSWERS a pending question
      about the goal itself (see that branch below).
    - `plan.suggested_action` set -> the note either accepts the
      proposed generic first step (see `_accepts_suggestion()`) or
      supplies new information about the goal (see that branch below).
    - `plan.suggested_duration` set -> the note confirms or overrides
      the agent's proposed default timeframe (see generate_plan()'s
      `suggested_duration` and apply_new_duration()).
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

    All of the above are checked before `parse_outcome()` runs, and for
    the same reason: `parse_outcome()`'s ACTION_COMPLETED_PHRASES
    already treats "yes"/"yeah"/"okay" as a completed Action -
    confirming a still-undone suggestion or answering a pending
    question must never be run through that classifier, or acceptance
    would be misread as completion (see docs/planning-model.md's ASK
    vs. SUGGEST). Context (which flag is set on `latest`), not the
    note's wording, is what decides the meaning.

    `note` is already read and stripped by the caller (frontend/app.py's
    feedback()). Which goal this applies to is `latest` itself - the
    caller resolves it from the form's `goal_id` (each active goal's
    card posts its own), not "whatever was touched most recently
    overall". With more than one active goal shown at once, that
    distinction is the difference between feedback landing on the goal
    you actually meant versus a different one entirely.

    A cancelled goal (see cancel_goal()) is a no-op here - returns
    `latest` unchanged rather than risking a save_plan() call that
    doesn't carry `cancelled` forward, which would silently revive it.
    """
    if latest.get("cancelled"):
        return latest

    duration = latest.get("duration")

    if latest["plan"].get("clarification"):
        # No real plan yet - `note` answers the clarifying question, not
        # a status report. Routed through generate_plan() (not replan(),
        # built around `now` completion; not parse_outcome(), which
        # would force an answer like "speed and comprehension" through
        # outcome categories that don't apply).
        #
        # Joins every prior answer, not just this note (same reasoning
        # as replan()'s full-history pass) - a multi-round clarification
        # needs all answers together, or the next call re-asks what's
        # already covered. Safe here: this branch only runs while
        # `clarification` keeps recurring, so every past `feedback` in
        # this goal's history is a prior answer.
        prior_answers = [r["feedback"] for r in get_history_for_goal(latest["goal_id"]) if r.get("feedback")]
        combined_goal = " - ".join([latest["goal"], *prior_answers, note])
        # `duration` can still be None here specifically when this
        # clarification IS create_goal()'s missing-timeframe question -
        # the answer is a duration phrase, not more goal content, so it
        # needs the same extraction create_goal() does, or it stays
        # lost as untyped prose. Skipped when duration is already known
        # (a content-vagueness clarification) - `note` there answers a
        # different question, not a timeframe to (mis)parse.
        if duration is None:
            duration = extract_duration_phrase(note)
        plan = planner.generate_plan(combined_goal, duration, vision_id=latest.get("vision_id"))
        # Same data-loss fix as the replan() branch below: a clarification
        # round that lands on ASK/SUGGEST again leaves generate_plan()'s
        # own steps/progression at their fresh-mint None, which would
        # otherwise silently wipe a progression tree built since the last
        # real plan (manual +/-, cold Suggest, chat-grounded suggest).
        if plan.get("steps") is None:
            plan["steps"] = latest["plan"].get("steps")
        if plan.get("progression") is None:
            plan["progression"] = latest["plan"].get("progression")
        # frozen_duration stays None for as long as clarification keeps
        # coming back (same reasoning as create_goal() above: nothing
        # has actually started yet) - only frozen for real, for the
        # first time, the moment a real plan finally comes back.
        return save_plan(
            latest["goal"], plan, feedback=note, duration=duration,
            goal_id=latest["goal_id"],
            frozen_duration=planner.frozen_duration_for(plan, duration),
            vision_id=latest.get("vision_id"),
        )

    if latest["plan"].get("suggested_action"):
        # A generic first move was proposed because the goal's content
        # wasn't specific enough to plan directly, but no blank
        # clarifying question was warranted either (see generate_plan()'s
        # `suggested_action`). `note` either accepts it, or supplies new
        # information that changes what should happen next.
        suggested_action = latest["plan"]["suggested_action"]
        if _accepts_suggestion(note):
            # Confirmation, not execution: the proposal becomes the
            # ordinary Action (`now`) - no replan(), no current_step/
            # step_status change, and the Action is not marked
            # completed (see docs/planning-model.md's ASK vs. SUGGEST -
            # "PLAN begins when..."). The next feedback on this goal has
            # no pending flags left, so it falls straight through to the
            # ordinary outcome path below, exactly like any other Action.
            new_plan = dict(latest["plan"])
            new_plan["now"] = suggested_action
            new_plan["suggested_action"] = None
            new_plan["clarification"] = None
            feedback_text = "Accepted the suggested action." + (f" Note: {note}" if note else "")
            return save_plan(
                latest["goal"], new_plan, feedback=feedback_text, duration=duration,
                goal_id=latest["goal_id"], frozen_duration=latest.get("frozen_duration"),
                current_step=latest.get("current_step", 0), vision_id=latest.get("vision_id"),
                step_status=latest.get("step_status"),
            )

        # Not a clear acceptance - `note` is either a stated substitute
        # ("I'd rather start with my CV") or new information correcting
        # the agent's premise ("I already have a list"). Both are
        # information the goal's content didn't carry before, so both
        # are handled the same way a clarification's answer is above:
        # re-evaluated from scratch, letting generate_plan() decide what
        # it now supports (a real plan, a new suggested_action, or a
        # genuine clarifying question) - deliberately not classified
        # further here (see docs/planning-model.md § ASK vs. SUGGEST,
        # Open questions).
        #
        # `note` itself is passed as `reply`, alongside `suggested_action`
        # as `prior_suggestion` (added 2026-09-08, experimental - see
        # docs/planning-model.md § Interpreting a response to
        # ASK/SUGGEST) - not folded into `combined_goal` the way earlier
        # rounds' feedback still is, so the model sees its own previous
        # suggestion and the user's actual reply as two explicit,
        # labeled things, rather than `note` arriving as unlabeled,
        # appended goal text indistinguishable from the goal itself.
        prior_answers = [r["feedback"] for r in get_history_for_goal(latest["goal_id"]) if r.get("feedback")]
        combined_goal = " - ".join([latest["goal"], *prior_answers])
        if duration is None:
            duration = extract_duration_phrase(note)
        plan = planner.generate_plan(
            combined_goal, duration, vision_id=latest.get("vision_id"),
            prior_suggestion=suggested_action, reply=note,
        )
        # Same data-loss fix as the clarification branch above and the
        # replan() branch below.
        if plan.get("steps") is None:
            plan["steps"] = latest["plan"].get("steps")
        if plan.get("progression") is None:
            plan["progression"] = latest["plan"].get("progression")
        return save_plan(
            latest["goal"], plan, feedback=note, duration=duration,
            goal_id=latest["goal_id"],
            frozen_duration=planner.frozen_duration_for(plan, duration),
            vision_id=latest.get("vision_id"),
        )

    if latest["plan"].get("pending_duration_question"):
        # The PREVIOUS record asked "how long do you want this to run
        # now?" - this note is the answer, not a status report. Falls
        # back to the existing duration if nothing recognized - never
        # silently wipes a working timeframe.
        new_duration = extract_duration_phrase(note) or duration
        return planner.apply_new_duration(latest, new_duration, feedback=note)

    if latest["plan"].get("suggested_duration"):
        # The PREVIOUS record proposed a default timeframe (see
        # generate_plan()'s `suggested_duration`) - this note either
        # confirms it as given (no recognizable duration phrase in the
        # reply falls back to the suggestion itself) or overrides it
        # with a different one. Reuses apply_new_duration() exactly as
        # a manual duration change would - no separate confirm path.
        new_duration = extract_duration_phrase(note) or latest["plan"]["suggested_duration"]
        return planner.apply_new_duration(latest, new_duration, feedback=note)

    if requests_duration_change(note):
        # A request to change the TIMEFRAME, not a progress report -
        # checked before parse_outcome() so it's never misread as one of
        # its outcomes (see requests_duration_change()'s docstring).
        # Applies immediately if the new duration is already IN this
        # message (e.g. "change timeframe to 1 hour"); only asks the
        # follow-up when nothing recognized turns up.
        new_duration = extract_duration_phrase(note)
        if new_duration:
            return planner.apply_new_duration(latest, new_duration, feedback=note)

        # Carries the current plan/duration/steps forward completely
        # unchanged (this goal isn't being replanned or checked in on
        # right now) - only difference from a plain "carry forward"
        # save is the pending_duration_question flag, which is what
        # makes the branch above fire on the NEXT message and is what
        # active_goal/_conversation.html's thread shows as the agent's reply
        # instead of the real `now`.
        return save_plan(
            latest["goal"],
            {**latest["plan"], "pending_duration_question": "How long do you want this to run now?"},
            feedback=note, duration=duration, goal_id=latest["goal_id"],
            frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
            vision_id=latest.get("vision_id"), step_status=latest.get("step_status"),
        )

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # frozen_duration.py §1). Falls back to computing one fresh only
    # for a goal saved before frozen_duration existed - a one-time
    # "adopt now", not a recurring recompute.
    frozen = latest.get("frozen_duration") or freeze_duration(duration)
    classified = parse_outcome(note)
    # Anything not confidently recognized defaults to the same safe
    # no-op as "action_in_progress" - check in without changing the
    # plan, rather than guess toward a riskier outcome
    # (action_completed/goal_completed) from ambiguous text. See
    # parse_outcome()'s docstring.
    outcome_value = classified or "action_in_progress"

    if outcome_value == "goal_completed":
        # The whole goal is done, not just this one "now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
            frozen_duration=frozen, vision_id=latest.get("vision_id"),
            current_step=latest.get("current_step", 0), step_status=latest.get("step_status"),
        )

    if outcome_value == "action_in_progress":
        # Mid-task, not stalled or failed - a distinct signal from "No"
        # (see docs/06-development.md, 2026-08-20, for the plan-drift
        # bug this fixed). No replan() call: check in without asking
        # the model to change anything. `classified` distinguishes "you
        # said you're still working on it" from "we couldn't tell" -
        # both get the same safe treatment, but the record stays honest
        # about which happened. The "couldn't tell" case asks the model
        # for a natural acknowledgment of `note` (acknowledge() -
        # display text only, can never change this branch or fail it).
        prefix = "Still working on it." if classified else acknowledge(note)
        feedback_text = prefix + (f" Note: {note}" if note else "")
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, goal_id=latest["goal_id"], frozen_duration=frozen,
            vision_id=latest.get("vision_id"),
            current_step=latest.get("current_step", 0), step_status=latest.get("step_status"),
        )

    outcome = "Completed the action" if outcome_value == "action_completed" else "Did not complete the action"
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    # The full chain, not just latest["plan"] - see replan()'s docstring
    # for why: a model only shown the single previous step has no way to
    # notice it has already shrunk `now` several times in a row.
    new_plan = planner.replan(
        latest["goal"], get_history_for_goal(latest["goal_id"]), feedback_text,
        duration=duration, vision_id=latest.get("vision_id"),
    )
    # replan() only ever returns PLAN_KEYS - REPLAN_SYSTEM_PROMPT never
    # mentions steps, so `new_plan` has no "steps" key at all. Carry the
    # existing step list, shadow progression, and pointer forward
    # unchanged rather than silently losing them on every real replan;
    # this is a data-loss fix, not a re-evaluation of whether the steps
    # still make sense (see docs/planning-model.md, "Feedback and
    # Replanning").
    new_plan["steps"] = latest["plan"].get("steps")
    new_plan["progression"] = latest["plan"].get("progression")
    # goal_id carried forward explicitly - without this, save_plan() would
    # mint a fresh one and this replan would silently start a *new*
    # goal entry instead of continuing the existing goal's chain.
    return save_plan(
        latest["goal"], new_plan, feedback=feedback_text, duration=duration,
        goal_id=latest["goal_id"], frozen_duration=frozen, current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"), step_status=latest.get("step_status"),
    )
