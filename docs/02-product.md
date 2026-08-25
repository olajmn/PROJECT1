# 02 — Product

> What the product actually is, concretely: what it does, what it's
> made of, what the MVP is, what's explicitly out of scope. Not how the
> system is built (see [[03-architecture]]) or what's actually
> implemented right now (see [[04-current-state]]) - trimmed 2026-08-25
> to stop mixing product definition with architecture notes and
> implementation status.

## 1. Product definition

> [[06-development]] § The Approach, Phase 4.

The product is currently being defined through the MVP and testing
process. The first user is the project owner, and the current product
hypothesis is expressed through the capabilities, user flow, and MVP
below.

## 2. User Flows

> [[06-development]] § The Approach, Phase 5. Builds on § Product definition above.

### Main flow (draft from the kickoff conversation)

```
New user
↓
States a goal
↓
Agent asks questions
↓
Agent creates a plan
↓
User approves
↓
Today's action
↓
Feedback
↓
Agent evaluates
↓
Next action
↓
Replanning
```

### Refined as a closed loop (see [[06-development]] § Hypothesis, Refined framing)

This isn't a one-time sequence — it's a loop that feeds back into memory
and starts again:

```
GOAL → PLAN → TODAY/RIGHT NOW → ACTION → USER FEEDBACK → REPLAN → ACTION → MEMORY ↺
```

"Prototype 0.1" (see § MVP below) is the smallest version of this that
actually closes the circle.

### Current status

**Target loop:** Goal → Plan → Action → Feedback → Replan.

See [[04-current-state]] for implementation status.

## 3. Capabilities

> See § Product definition above for what the agent should/shouldn't
> do. These are possible capabilities, not a committed roadmap - see
> § Non-goals below and [[06-development]] § Parking Lot for what's
> deliberately deferred.

### Candidate list (from the core idea description)

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
proves the hypothesis in [[06-development]] § Hypothesis, defer the
rest to [[06-development]] § Parking Lot.

### Refined long-term capability list (2026-08-18)

More precise naming for the same idea, from a parallel ChatGPT
discussion — capabilities the agent could eventually have, explicitly
**not built simultaneously**:

- Goal interpretation
- Planning
- Replanning
- Task decomposition
- User interaction
- Memory
- Temporal awareness (see [[03-architecture]])
- Information retrieval / aggregation (a *capability* the agent can call
  on, not the core product — e.g. weather, calendar, maps, resources —
  see [[06-development]] § Parking Lot)
- Personal knowledge base — see § Personal knowledge below
- Proactive notifications
- Reflection
- Progress tracking

### Personal knowledge (2026-08-22, sketched — not built)

A possible future capability is allowing the agent to use documents
supplied by the user (e.g. text files with documented science behind
them) as contextual knowledge when reasoning about a goal or plan - not
just the model's own training, not a live internet search either.
Distinct from "Information retrieval / aggregation" above
(weather/calendar/maps - live *external* data) - this is the user's
*own*, offline, supplied material.

Technical implementation (the RAG mechanism, sketched pipeline, storage
approach): [[03-architecture]] § Knowledge.

## 4. MVP

> [[06-development]] § The Approach, Phase 7. See § User Flows above for the full flow.

**This is "Prototype 0.1"** — the smallest version of the full agent
loop in [[06-development]] § Hypothesis that closes the circle (goal →
plan → action → feedback → replan → next action). Not a one-time plan
generator.

### Target flow for the MVP

```
User writes a goal
↓
LLM creates a plan
↓
Plan is saved
↓
User gets today's task
↓
User reports progress
↓
LLM can adjust the plan
```

### Status

Prototype 0.1's loop first closed end-to-end 2026-08-18 (see
[[06-development]] for the log entry). See [[04-current-state]] for
current implementation status. Next: real usage/testing (see Testing
philosophy below), not more features.

**Important distinction:** implemented doesn't mean the agent's answers
are always accurate. The model has already been caught hallucinating a
specific, unfounded detail (see [[06-development]] § Experiments) - the
mechanism working and the output being reliable are two different
things. Don't conflate them when reporting progress.

### Testing philosophy

First user is the project owner, testing on themselves. Explicitly
**not needed** to test the core hypothesis: web app, mobile app, voice,
cloud, advanced UI, an aggregator system, or an advanced memory database.
The question that matters right now:

> Can the agent actually help me do something I would otherwise have
> struggled to do?

If Prototype 0.1 works well → build further. If it doesn't → find out
why before building more. Testing takes priority over further
ideation — see [[05-decisions]].

## 5. Non-goals

We shouldn't start with "how do we build the complete agent?" - that's
too big. We also shouldn't decide that this has to become a startup.
And we shouldn't assume the idea is good just because it feels
exciting. We're going to test the hypothesis instead - see § Testing
philosophy above and [[06-development]] § Hypothesis.

## See also

- [[00-project-brief]]
- [[03-architecture]]
- [[06-development]]
