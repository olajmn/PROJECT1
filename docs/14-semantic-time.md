# 14 — Semantic Understanding of Time

> Draft, 2026-08-24. Expands the "semantic understanding of time" idea
> first logged in [[13-ideas-parking-lot]] the same day.
>
> **2026-08-25: first piece built.** `relative_length()` in
> `backend/agent/distributed/temporal/relative_time.py` answers the
> "relative duration" half of the idea (see "The core idea" point 2
> below) - deterministic, placed in the Time faculty. The
> "activity-specific meaning" half (point 1 below) is still fully
> unbuilt and unresolved - see "Open design questions" below for what
> that decision narrowed down, and what's still genuinely open.

## The core idea

The agent today only knows time as a number or a resolved clock
window (see [[08-technical-architecture]] § Faculties -
`backend/agent/distributed/temporal/`). `resolve_duration("1 hour")`
always means exactly 60 minutes, no matter what it's 60 minutes *of*.

A human doesn't experience duration that way. Two things are true at
once, and neither is captured by a raw number:

1. **The same duration means different things depending on the
   activity.** One hour of reading is a lot. One hour of training is
   comparatively little. The number is identical; what it *represents*
   isn't.
2. **The same duration is long or short depending on what it's
   compared to.** One hour is long next to 15 minutes, short next to a
   full day. There's no fixed "long" or "short" - only relative to a
   scale.

## Why this matters for planning, specifically

This isn't just a description problem - it changes what the agent
should *do*. Today, if a plan needs to shrink (see [[12-decisions]]'s
"only shrink once" fix, and the still-parked "Plan as an ordered step
list" idea in [[13-ideas-parking-lot]]), the only move available is
shrinking the existing plan: less time, same shape.

The concrete example from the original brainstorm: if the user only
has 45 minutes available, the agent shouldn't automatically assume
"same plan, smaller." A 45-minute reading session and a 45-minute gym
session aren't the same kind of *smaller* - depending on the goal, 45
minutes might call for a genuinely different activity or plan shape,
not a shorter version of the one already chosen.

## Open design questions

- **Where does "what this duration means" come from?** RESOLVED for
  the relative-duration half (point 2 in "The core idea" above):
  deterministic, hardcoded thresholds
  (`_RELATIVE_LENGTH_THRESHOLDS` in `relative_time.py`) - the "code
  decides, model is just told" principle ([[12-decisions]],
  2026-08-20) applies here too, not in tension with it after all.
  STILL OPEN for the activity-specific half (point 1): lookup table vs.
  model-informed reasoning, not decided, not built.
- **Is this actually part of the Time faculty, or a different one?**
  RESOLVED, but only for the relative-duration half: it lives in
  `backend/agent/distributed/temporal/relative_time.py` - pure magnitude
  comparison needs no knowledge of activities, so it fits Time
  cleanly. The activity-specific half is STILL OPEN, and still looks
  like it belongs to a Language/Semantics faculty that doesn't exist
  yet, not Time - `relative_time.py`'s own docstring is explicit that it
  says nothing about what either span is FOR.
- **What does "relative" duration require?** RESOLVED: a second
  duration string to compare against (`reference` in
  `relative_length(duration, reference)`), resolved the same way via
  `resolve_span()` - not `broadest_relevant_horizon()`'s bucket
  system after all, a simpler direct ratio instead. Nothing calls
  `relative_length()` yet - no caller passes a real `reference` (the
  goal's overall duration, a previous step's length, etc.) in
  practice yet.
- **What's the actual trigger?** STILL OPEN. `relative_length()` exists
  as a capability, but isn't wired into `plan.py`/`replan()` or the UI
  anywhere yet - whether it runs on every plan generation or only when
  a plan shrinks is still undecided, because nothing calls it yet.

## Built so far

`backend/agent/distributed/temporal/relative_time.py` -
`relative_length(duration, reference)` returns `"short"`/`"medium"`/
`"long"` based on a fixed, tunable ratio table, or `None` if either
side doesn't resolve to a real span. Not yet wired into any caller
(`plan.py`, `replan()`, the UI) - see "What's the actual trigger?"
above. The activity-specific half of the original idea (point 1 in
"The core idea") is untouched - no code, no schema, no prompt changes.

## See also

- [[13-ideas-parking-lot]] - original brainstorm entry, same day
- [[08-technical-architecture]] § Faculties - Time faculty, and the
  Language/Semantics faculty this may partly belong to instead
- [[12-decisions]], 2026-08-20 - "code decides, model is just told,"
  the principle in tension with itself here
