# 00 — Project Brief

> What this project is trying to be — its identity, vision, and central
> question. This document describes what the project is trying to become,
> not how it was built or what is true right now.
>
> See [[06-development]] for the project's development history and
> [[04-current-state]] for its current state.

## 1. The Core Idea

The project is an AI agent that helps people go from what they want to achieve to what they actually do.

The user should, in principle, only need to say things like:

> "I want to learn backend development."
> "I want to get in better shape."
> "I want to start a company."
> "I want to clean the apartment today."

The agent should then understand the goal, break it down, create a plan, and continuously help the user carry it out.

The central idea is therefore not primarily:

> AI that creates plans.

But rather:

> AI that takes responsibility for the planning and continuously translates goals into action.

## 2. The Bigger Vision

The long-term vision is a personal agent that tries to increase the probability that the user actually does things that are good for them.

The agent can potentially operate across many different timescales:

```text
10 years
 ↓
5 years
 ↓
1 year
 ↓
3 months
 ↓
1 month
 ↓
1 week
 ↓
today
 ↓
now
 ↓
next action
```

These can be described as different time horizons / levels of granularity.

Example:

> "I want to become a backend developer."

can become:

- **Within one year** → get a relevant job
- **This month** → build a project
- **This week** → finish the backend
- **Today** → implement an API endpoint
- **Now** → open VS Code and create the file

The interesting part is the zooming from an abstract goal to a concrete action.

## 3. What Sets This Apart From a Regular Todo App

A regular todo app says:

> "Here are your tasks."

An AI planner says:

> "Here's the plan I made for you."

The proposed agent should go further:

> "I'm following the process together with you and deciding what should happen next."

It should be able to:

- understand goals
- break goals down
- prioritize
- create tasks
- track progress
- detect deviations
- replan
- adapt to the user's situation
- choose the right granularity
- communicate proactively
- reduce how much project-managing the user has to do themselves

The real value is therefore:

> Reducing the amount of planning and decision-making work the user has to do themselves.

## 4. Example User Experience

The user:

> "I want to start working out."

The agent might ask:

> "What do you want to achieve, and how much time do you have available?"

It can then create a plan.

But when the plan is to be executed, it can go all the way down to action:

1. Get up from the couch.
2. Find workout clothes.
3. Put on shoes.
4. Fill the water bottle.
5. Go outside.
6. Walk to the gym.

The point isn't necessarily that every task should always be broken down this far.

The point is that the agent should be able to decide how much help the user needs right now.

It could be:

> "Work out for 45 minutes."

or:

> "Find your running shoes."

## 5. The Agentic Part

This is the technically interesting part.

A simple AI function:

```text
Input
↓
LLM
↓
Output
```

An agent:

```text
Goal
↓
Plan
↓
Observes the situation
↓
Makes a decision
↓
Acts
↓
Observes the result
↓
Replans
↓
Acts again
```

The agent will require mechanisms for memory, state, planning, time, communication and eventually action. The exact technical implementation is deliberately left open — see [[03-architecture]] for what's actually been built.

It's the system around the LLM that makes an agent harder to build than a simple AI function.

The project does not require building or training its own foundation model.

## 6. How Hard Is It?

### A possible first version

Relatively achievable.

A first version could be:

```text
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

This is a realistic project to build while learning backend development.

### Full vision

Significantly harder.

The challenges include:

- good long-term planning
- realistic plans
- context
- memory
- timing
- proactivity
- replanning
- personalization
- the right granularity
- not becoming annoying
- knowing when the agent should intervene
- knowing when it should leave the user alone

The hardest part is therefore probably not connecting to an LLM.

The hardest part is:

> Building an agent that actually feels useful over time.

## 7. Product Philosophy

We've also identified something important:

This doesn't have to be a classic "lifestyle app."

It shouldn't necessarily be:

> sleep + fitness + diet + finances + mindfulness + productivity + everything.

The core can be much cleaner:

> You tell the agent what you want to accomplish. The agent helps you actually get it done.

The life domain is secondary.

It can be used for:

- personal development
- studying
- programming
- fitness
- projects
- work
- hobbies
- practical tasks

## 8. Possible Long-Term Positioning

A possible brand/product position could be something along the lines of:

> "The thing that helps you actually do what you say you're going to do."

Not necessarily an "AI planner."

Not necessarily a "life coach."

But an execution agent.

The Duolingo example we discussed is relevant here: the technology behind language learning isn't unique, but the product can achieve a very strong position through UX, identity, habit, and brand.

The same could be possible here.

## 9. The Most Important Question Right Now

We've actually moved from:

> "I have an idea for an AI planner."

to a much more interesting hypothesis:

> Can we build an agent that means the user needs to spend significantly less mental energy planning, prioritizing, and organizing the path from goal to actual action?

That's what this project should investigate.

And we don't need to know the answer in advance.

If we research the market and discover someone has already solved this perfectly → great, we've learned that.

If we find a gap → we build.

If we find that the problem is interesting but our solution is wrong → we change it.

So the first idea doesn't have to be the final idea.

## Short version

**Vision:**

A personal AI agent that helps people go from "this is what I want to achieve" to "this is what I'm doing now."

**Core:**

Goal → plan → action → feedback → replanning.

**Differentiation hypothesis:**

Not just planning, but agentic execution.

**Central question:**

Can we build an agent that meaningfully reduces the mental effort required to turn goals into action?

And the most important rule:

> We're not trying to prove the idea is good. We're trying to find out if it's good.

## See also

- [[01-research]] — the problem, and what exists outside this project (moved out 2026-08-25, was part of this brief)
- [[02-product]] — the concrete product definition, user flows, features, MVP, and what's explicitly out of scope right now
- [[06-development]] — the original phased approach, and everything that's actually happened since
- `../COLLABORATION.md` — how documentation and collaboration work in this project
- [[04-current-state]] — what's true right now
