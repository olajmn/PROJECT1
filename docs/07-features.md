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

## See also

- [[09-mvp]] — what's actually chosen for the MVP
