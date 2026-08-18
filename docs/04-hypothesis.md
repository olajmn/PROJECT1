# 04 — Hypothesis

> Phase 3 in [[00-project-brief]].

## Template

> "We believe that ..."

## Current hypothesis (draft from the kickoff conversation)

> We believe that people don't primarily need help creating plans, but
> help continuously translating plans into concrete actions.

And more specifically (the question the project should investigate):

> Can we build an agent that means the user needs to spend significantly
> less mental energy planning, prioritizing, and organizing the path from
> goal to actual action?

## Refined framing (from a parallel ChatGPT discussion, 2026-08-18)

The project is a **personal agent**, not a planning app. Planning is one
capability the agent uses, not the product itself. The hypothesis is
really about a continuous loop, not a one-time plan:

```
GOAL → PLAN → TODAY/RIGHT NOW → ACTION → USER FEEDBACK → REPLAN → ACTION → MEMORY ↺
```

**"Prototype 0.1"** = the smallest version of this loop that actually
closes the circle back into a new action:

```
User gives goal → Agent creates plan → Agent gives concrete action →
User performs / doesn't perform it → User gives feedback → Agent
interprets feedback → Agent changes the plan → Agent gives next action
```

This reframes what's actually being tested: not "can an LLM make a
plan" (trivial, already proven) but **"does closing this feedback loop
create real value for the user."** See [[09-mvp]] for build status.

## How we test it

*(to be filled in — which experiments/user tests confirm or disprove this?)*

- See [[11-experiments]]

## Status

- [ ] Not tested yet
- [ ] Partially supported
- [ ] Disproven — see why below

## See also

- [[01-problem]]
- [[03-competitors]] — informs the hypothesis
- [[05-product]] — the hypothesis drives the product definition
