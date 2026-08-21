# 07 — Features

> See [[05-product]] for what the agent should/shouldn't do.

## Candidate list (from the core idea description)

The agent should potentially be able to:

- [ ] understand goals (natural language input)
- [ ] break goals down (multiple time horizons)
- [ ] prioritize
- [ ] create tasks
- [ ] track progress
- [ ] detect deviations
- [ ] replan
- [ ] adapt to the user's situation
- [ ] choose the right granularity
- [ ] communicate proactively
- [ ] reduce how much project-managing the user has to do themselves

**Don't build all of it.** This list is a menu, not a spec — pick what
proves the hypothesis in [[04-hypothesis]], defer the rest to
[[13-ideas-parking-lot]].

## Refined long-term capability list (2026-08-18)

More precise naming for the same idea, from a parallel ChatGPT
discussion — capabilities the agent could eventually have, explicitly
**not built simultaneously**:

- Goal interpretation
- Planning
- Replanning
- Task decomposition
- User interaction
- Memory
- Temporal awareness (see [[08-technical-architecture]])
- Information retrieval / aggregation (a *capability* the agent can call
  on, not the core product — e.g. weather, calendar, maps, resources —
  see [[13-ideas-parking-lot]])
- Proactive notifications
- Reflection
- Progress tracking

## Architecture framing: Program / Rooms / Sitemap (2026-08-21)

The user's own framing, borrowed from building architecture, for
thinking about what the agent actually is - kept here as the product
definition, and as the mental model to build from going forward.

**Program** (what the building is for):
> The agent should help a person go from a goal to a concrete plan.

**Rooms** (the functions the building needs - mapped to what already
exists in code):

| Room | What it is today |
|---|---|
| Goals | `goal` + `goal_id` (`backend/storage.py`) |
| Plans | the `plan` dict: `one_year` / `one_month` / `this_week` / `right_now` |
| Tasks | not yet its own room - see "right_now is a trigger, not a time variable" below |
| Time periods | `duration` + `_resolve_duration()` (`backend/timeperiod.py`) |
| Conversation | the You/Agent thread on each active goal (`_active_goal.html`) |
| History | `get_history_for_goal()` / the `/history` log |

**Sitemap** (how the rooms connect):

```
user -> agent -> goals -> plans -> [year, month, week, day, hour, minute]
```

The time axis (year down to minute) is a pure *when* hierarchy - it
doesn't exist as real structure yet (see
[[08-technical-architecture]] § Memory & Data Architecture's
folder-per-time-period idea, parked, not built). Today's `plan` dict
only has three rungs on it (`one_year`/`one_month`/`this_week`), with
nothing between "this week" and `right_now`.

**`right_now` is a trigger, not a time variable.** It doesn't belong on
the same axis as year/month/week/day/hour/minute - those describe a
shrinking window of *when*; `right_now` is the *action* that fires once
the time hierarchy has resolved all the way down to the present
moment. Treating it as just the smallest time-horizon (as `PLAN_KEYS`
currently does, listing it alongside `one_year`/`one_month`/`this_week`
as if it were a peer) blurs two different things: a description of a
time window, versus the actual task to execute. This is "Tasks" as its
own room in the table above - not built yet as a distinct concept from
`right_now`, but this is the reasoning for why it should eventually be
one.

## See also

- [[09-mvp]] — what's actually chosen for the MVP
