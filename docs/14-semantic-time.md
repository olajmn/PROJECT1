# 14 — Semantic Understanding of Time

> Draft, 2026-08-24. Expands the "semantic understanding of time" idea
> first logged in [[13-ideas-parking-lot]] the same day. Not designed
> or built - this is the starting point for that design conversation,
> not the result of one.

## The core idea

The agent today only knows time as a number or a resolved clock
window (see [[08-technical-architecture]] § Faculties -
`backend/agent/distributed/timeperiod/`). `resolve_duration("1 hour")`
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

## Open design questions - none of these are answered yet

- **Where does "what this duration means" come from?** Two very
  different approaches, with the project's existing "code decides,
  model is just told" principle ([[12-decisions]], 2026-08-20) in
  tension with itself here:
  - A lookup/table approach (deterministic): some notion of typical
    session length per activity type, so the code itself can say "45
    minutes is short for running, long for stretching." Needs a real
    source for these norms - not obviously something code can just
    know, unlike a calendar date.
  - A model-informed approach: give the LLM richer context (the goal's
    activity type, the requested duration, and how that compares to a
    "typical" session for that kind of activity) and let it reason
    about fit, rather than have code pre-judge "short" or "long."
    Tension: this project has repeatedly moved AWAY from letting the
    model judge things code could decide instead (see the horizon-scope
    fix, outcome classification, [[12-decisions]]) - it's not obvious
    this is the same kind of decision or a different one.
- **Is this actually part of the Time faculty, or a different one?**
  [[08-technical-architecture]] § Faculties flags this exact tension:
  Time (`timeperiod/`) understands *when*, grounded in clock time and
  calendar dates - deterministic, verifiable, no notion of "activity."
  "What does this duration mean for this activity" needs to know about
  the activity itself, which sounds closer to a Language/Semantics
  faculty (also unbuilt, also just a name so far) than to Time.
  Possibly two faculties cooperating, not one faculty doing both jobs.
- **What does "relative" duration require?** "Long compared to what?"
  needs some reference scale - the goal's own overall duration
  (this connects to `broadest_relevant_horizon()` in
  `backend/agent/distributed/timeperiod/frozen.py`, which already
  computes a coarse duration-scale bucket for a different purpose -
  possibly reusable, possibly a coincidence of shape, not decided).
- **What's the actual trigger?** Does this run every time a plan is
  generated, or only when a plan needs to *shrink* (the concrete
  scenario in the original brainstorm)? Those are different scopes -
  "always understand duration semantically" vs. "when shrinking,
  consider a different shape, not just a smaller one."

## Not started

No code, no schema, no prompt changes. This is deliberately just the
shape of the problem and the real tensions in solving it - the design
conversation itself (which approach, which faculty, which trigger)
hasn't happened yet.

## See also

- [[13-ideas-parking-lot]] - original brainstorm entry, same day
- [[08-technical-architecture]] § Faculties - Time faculty, and the
  Language/Semantics faculty this may partly belong to instead
- [[12-decisions]], 2026-08-20 - "code decides, model is just told,"
  the principle in tension with itself here
