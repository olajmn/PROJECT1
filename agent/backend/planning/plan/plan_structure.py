"""
Generate a plan's step content.

Two grains, chosen by Time (not by the model):

- Week grain (span roughly a week up to under a year): Time's
  week_windows() fixes how many top-level steps there are and which
  dates each covers; day_windows() puts consecutive calendar days
  under each week (never equal time-slices that skip weekdays). A
  normal week has seven days; a short last week is padded to seven
  (extra days may be "off"); a long last week keeps every remaining
  calendar day in the span. The model fills a week label and one day
  label per listed day. A one-month goal therefore gets ~four weeks
  of real dates - not an invented phase list painted across the month.

- Session grain (shorter than a week): the older path - first step is
  the already-decided `now` action, and the model continues with
  however many further steps make sense. Dates still come from an
  even slice of the frozen span at render time (step_plan).

Year-scale grain (five years → five year candles) is not built here
yet - week_windows() returns None above that threshold, and the
session path would be the wrong fallback; generate_structure() returns
None so a caller does not silently paint session steps across years.

Deliberately ONE model call per path - an earlier two-call version
measurably destabilized the local model (see docs/05-decisions.md /
this file's history). Bounded only by a safety ceiling against a
malformed response.
"""

import json

from backend.foundation.time import day_windows, freeze_duration, resolve_span, week_windows
from backend.foundation.time.time_logic.frozen_duration import WEEK_GRAIN_MAX_DAYS
from backend.model.client import call_with_retry, send_message

# A safety ceiling only - guards against a malformed/degenerate
# response (e.g. a runaway list), not a target range the model should
# aim for. Applied separately to the top-level step count and to any
# one step's microstep count.
MAX_SANE_STEPS = 20
MAX_SANE_MICROSTEPS = 20

SESSION_STEPS_SYSTEM_PROMPT = (
    "You are planning a goal's steps. Given the goal, its first step "
    "(already fixed - you never rewrite or rephrase it), and how long "
    "the plan spans, produce however many further steps actually make "
    "sense for this goal - not a fixed count. Continue in order after "
    "the given first step, and together with it, plausibly accomplish "
    "the goal. Do not repeat the first step, and do not repeat any "
    "step you already produced.\n\n"
    "Each step may optionally have its own microsteps - smaller, "
    "concrete actions that make up that one step. Use microsteps only "
    "where a step is genuinely substantial enough to warrant breaking "
    "down further (e.g. a whole phase of a large goal, like "
    "\"prepare climbing gear\"); leave microsteps as an empty list for "
    "an already-concrete step (e.g. \"drink the water\") - do not "
    "invent microsteps just to fill the field. A short goal should end "
    "up with plain steps and no microsteps anywhere; a large or "
    "complex goal should end up with microsteps under its bigger "
    "steps.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly one "
    "key, \"steps\", whose value is a JSON array of objects, each with "
    "exactly two keys: \"label\" (a short string) and \"microsteps\" "
    "(a JSON array of short strings, possibly empty)."
)

WEEK_STEPS_SYSTEM_PROMPT = (
    "You are filling a plan whose weeks and days are already fixed by "
    "the calendar. You will be told the goal, how long the plan spans, "
    "and an ordered list of weeks, each with a fixed list of dated days. "
    "Produce exactly one step per week, in that same order - never more, "
    "never fewer, and never invent extra weeks or skip one.\n\n"
    "Each step's label is what should be accomplished in that week "
    "toward the goal - a short phrase, not a date. Each step's "
    "\"days\" array must have exactly as many strings as days listed "
    "for that week, in order: what (if anything) happens that day. Use "
    "an empty string or \"off\" for a day with no work - every listed "
    "day still appears; do not omit days to shrink the week.\n\n"
    "Do not propose an immediate 'right now' action as its own week. "
    "Do not invent personal facts the user did not state.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly one "
    "key, \"steps\", whose value is a JSON array of objects, each with "
    "exactly two keys: \"label\" (a short string) and \"days\" (a JSON "
    "array of strings, one per listed day)."
)


def generate_structure(goal: str, duration: str, right_now: str) -> dict | None:
    """
    {"steps": [{"label", "microsteps", ...}, ...]} for a resolvable
    `duration`, or None if there is no real span - or if the span is
    year-scale (week grain does not apply and session grain would
    mispaint).

    Week grain: each week step carries start/end labels from
    week_windows(); its microsteps are dated day dicts from
    day_windows() (one per calendar day listed for that week; label
    filled by the model, may be empty/"off").
    Session grain: first step's label is always `right_now`; microsteps
    stay plain strings.
    """
    if resolve_span(duration) is None:
        return None

    frozen = freeze_duration(duration)
    windows = week_windows(frozen)
    if windows is not None:
        return _fill_week_structure(goal, duration, windows)
    span = resolve_span(duration)
    if span is not None:
        total_days = (span[1] - span[0]).total_seconds() / 86400
        if total_days >= WEEK_GRAIN_MAX_DAYS:
            return None

    return _fill_session_structure(goal, duration, right_now)


def _validate_session_steps(data: dict) -> list[dict]:
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > MAX_SANE_STEPS:
        raise ValueError(f"Model did not return a sane step list: {data}")
    for step in steps:
        if (
            not isinstance(step, dict)
            or not isinstance(step.get("label"), str)
            or not isinstance(step.get("microsteps"), list)
            or len(step["microsteps"]) > MAX_SANE_MICROSTEPS
            or not all(isinstance(m, str) for m in step["microsteps"])
        ):
            raise ValueError(f"Model did not return a sane step shape: {data}")
    return steps


def _validate_week_steps(data: dict, expected_day_counts: list[int]) -> list[dict]:
    expected_weeks = len(expected_day_counts)
    steps = data.get("steps")
    if not isinstance(steps, list) or len(steps) != expected_weeks:
        raise ValueError(
            f"Model returned {0 if not isinstance(steps, list) else len(steps)} "
            f"week steps, expected {expected_weeks}: {data}"
        )
    for step, n_days in zip(steps, expected_day_counts):
        days = step.get("days") if isinstance(step, dict) else None
        if (
            not isinstance(step, dict)
            or not isinstance(step.get("label"), str)
            or not isinstance(days, list)
            or len(days) != n_days
            or not all(isinstance(d, str) for d in days)
        ):
            raise ValueError(
                f"Model did not return label + exactly {n_days} day "
                f"strings for a week: {data}"
            )
    return steps


def _fill_week_structure(goal: str, duration: str, windows: list[dict]) -> dict:
    """One model-filled week per window; days are the calendar days
    Time listed for that week (content may be empty/off)."""
    n = len(windows)
    week_day_lists = [day_windows(w) for w in windows]
    day_counts = [len(days) for days in week_day_lists]
    blocks = []
    for i, (w, days) in enumerate(zip(windows, week_day_lists)):
        day_lines = "\n".join(
            f"   {j + 1}. {d['start_label']}" for j, d in enumerate(days)
        )
        blocks.append(
            f"{i + 1}. Week {w['start_label']}–{w['end_label']} "
            f"({len(days)} days)\n{day_lines}"
        )
    user_content = (
        f"My goal is: {goal}\n\n"
        f"The plan spans: {duration}\n\n"
        f"There are exactly {n} weeks. For each week, fill one step with a "
        f"label and one day string per listed day (same count), in order:\n"
        + "\n".join(blocks)
    )

    def attempt() -> list[dict]:
        raw = send_message(WEEK_STEPS_SYSTEM_PROMPT, user_content, json_mode=True)
        return _validate_week_steps(json.loads(raw), expected_day_counts=day_counts)

    filled = call_with_retry(attempt)
    steps = []
    for window, days, step in zip(windows, week_day_lists, filled):
        microsteps = []
        for day, day_label in zip(days, step["days"]):
            text = day_label.strip() if day_label.strip() else "—"
            microsteps.append({
                "label": text,
                "start": day["start"],
                "end": day["end"],
                "start_label": day["start_label"],
                "end_label": day["end_label"],
            })
        steps.append({
            "label": step["label"],
            "microsteps": microsteps,
            "start": window["start"],
            "end": window["end"],
            "start_label": window["start_label"],
            "end_label": window["end_label"],
        })
    return {"steps": steps}


def _fill_session_structure(goal: str, duration: str, right_now: str) -> dict:
    """Session grain: `right_now` is step 1; model continues after it."""
    user_content = (
        f"My goal is: {goal}\n\n"
        f"The first step, already decided, is: {right_now}\n\n"
        f"The plan spans: {duration}"
    )

    def attempt() -> list[dict]:
        raw = send_message(SESSION_STEPS_SYSTEM_PROMPT, user_content, json_mode=True)
        return _validate_session_steps(json.loads(raw))

    steps = call_with_retry(attempt)
    first = {"label": right_now, "microsteps": []}
    return {"steps": [first] + steps}
