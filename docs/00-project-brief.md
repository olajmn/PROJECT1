# Project: Personal AI Agent for Goal → Action

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

```
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

```
Input
↓
LLM
↓
Output
```

An agent:

```
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

The agent therefore eventually needs:

- an LLM
- memory
- a database
- user data
- state
- planning logic
- tools/APIs
- a time/event system
- replanning
- communication
- possible calendar integration
- notifications

It's the system around the LLM that makes an agent harder to build than a simple AI function.

We don't need to train our own AI model. The first version can use an existing API, for example from OpenAI or Anthropic.

## 6. How Hard Is It?

### MVP

Relatively achievable.

A first version could be:

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

This is a realistic project to build while learning backend development.

### Full Vision

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

## 7. The Competitive Landscape

We've already established that the core idea isn't new.

Several products work on:

- goal → milestones
- goal → daily tasks
- AI planning
- replanning
- personal coaching
- agentic planning
- long time horizons

Examples we've looked at include Goaltree, LifePilot, Mentra, Daysfold, Goaliath, GoalsFlow, Skedul.AI, Vakit, and GoalOS.

So we shouldn't build this project on the assumption that no one has done this before.

Instead, we should investigate:

> How good are they, really?

and:

> What do they NOT do?

## 8. The Competitive Analysis

We shouldn't just read the marketing copy.

We should compare the products systematically across factors like:

| Factor | Question |
|---|---|
| Goal input | Can the user just describe the goal naturally? |
| Long-term planning | Can the system plan over months/years? |
| Decomposition | How well is the goal broken down? |
| Granularity | How small can the actions get? |
| Daily execution | What does the user actually get to do today? |
| Agent | Does the system make its own decisions? |
| Replanning | What happens when the plan breaks? |
| Memory | Does the system remember the user's history? |
| Context | Does the system understand the user's situation? |
| Proactivity | Does the agent reach out on its own? |
| Tools | Can the agent actually perform actions? |
| Autonomy | How much project-managing does the user still have to do? |

This is where we'll try to find our differentiation.

## 9. Product Philosophy

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

## 10. Possible Long-Term Positioning

A possible brand/product position could be something along the lines of:

> "The thing that helps you actually do what you say you're going to do."

Not necessarily an "AI planner."

Not necessarily a "life coach."

But an execution agent.

The Duolingo example we discussed is relevant here: the technology behind language learning isn't unique, but the product can achieve a very strong position through UX, identity, habit, and brand.

The same could be possible here.

## 11. What We Are NOT Going to Do Right Now

We shouldn't start with:

> "How do we build the complete agent?"

That's too big.

We also shouldn't decide that this has to become a startup.

And we shouldn't assume the idea is good just because it feels exciting.

We're going to test the hypothesis.

## 12. The Approach

Here's how I'd set up the project:

### Phase 1 — Problem

Define, very concretely:

> What problem are we solving?

### Phase 2 — Research

Investigate existing solutions.

Map out:

- competitors
- features
- user experience
- weaknesses
- reviews
- what users are actually asking for

### Phase 3 — Hypothesis

Formulate:

> "We believe that ..."

Example:

> "We believe that people don't primarily need help creating plans, but help continuously translating plans into concrete actions."

### Phase 4 — Product Definition

Decide:

- who the first user is
- what problem the MVP solves
- what the agent does
- what the agent does NOT do
- what the user does
- what the "minimum useful product" is

### Phase 5 — User Flow

Map out the whole journey:

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

### Phase 6 — Technical Design

Now we start figuring out:

- frontend
- backend
- database
- LLM API
- agent architecture
- authentication
- scheduling
- notifications
- memory
- APIs/tools

### Phase 7 — MVP

Build the smallest version that actually demonstrates the idea.

Don't build everything.

### Phase 8 — Testing

Let real people use it.

Look especially for:

> "What does the agent do that actually helps?"

and:

> "When does the agent just become annoying?"

### Phase 9 — Iteration

Keep building based on actual usage.

## 13. How We'll Document the Project

We also concluded that you should use several tools with different roles:

### Paper

Thinking.

Brainstorming, sketches, questions, random ideas.

### Obsidian

Understanding and documenting.

The project's permanent knowledge base.

Suggested structure:

- 01 Problem
- 02 Research
- 03 Competitors
- 04 Hypothesis
- 05 Product
- 06 User flows
- 07 Features
- 08 Technical architecture
- 09 MVP
- 10 Development
- 11 Experiments
- 12 Decisions
- 13 Ideas / Parking lot

### Excel

Structuring and comparing.

Especially:

- competitors
- features
- research
- assessments
- experiments

### GitHub

Building and documenting the software itself.

### Meta-coherence

A loose guideline, not a rule (2026-08-24): documentation counts as
real project information, not scratch, even though it isn't code - the
reasoning behind a decision, or the shape of an idea before it's
built, is still part of what the project actually is. This doesn't
mean every file needs a matching write-up somewhere - it means the
vault as a whole, especially anything that could potentially become
public, should read as one coherent, connected thing rather than
disconnected fragments.

Nothing new to adopt - just naming how this vault already works:

- Cross-linked via `[[references]]` rather than left as isolated files
- Historical, dated entries preserved as accurate records of what was
  true when written, rather than rewritten once something later
  changes (see [[12-decisions]])
- Code and docs reference each other in both directions - a docstring
  points to the doc that explains why, a doc points to the file that
  implements it

## 14. The Most Important Question Right Now

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

## Short Version

**Vision:**

A personal AI agent that helps people go from "this is what I want to achieve" to "this is what I'm doing now."

**Core:**

Goal → plan → action → feedback → replanning.

**Differentiation hypothesis:**

Not just planning, but agentic execution.

**First MVP:**

The user states a goal → the agent creates a plan → the agent picks today's next action → the user gives feedback → the agent adapts the plan.

**Working method:**

Research → competitive analysis → hypothesis → product design → MVP → testing → iteration.

And the most important rule:

> We're not trying to prove the idea is good. We're trying to find out if it's good.
