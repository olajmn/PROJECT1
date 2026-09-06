# Planning Model

> Working conceptual model for what a Goal's plan actually means in this agent — not a technical specification, a data model, or a system prompt. Concepts below are labeled **fact** (confirmed in the running prototype), **hypothesis** (a working idea, not yet decided), **limitation** (a confirmed gap in current behavior), or **open question** (deliberately unresolved) — the same taxonomy as `global-standards/DOCUMENTATION_STYLE_GUIDE.md` §5. Most of what follows is hypothesis: this document exists to give planning a shared vocabulary to reason with, not to record a settled architecture. Nothing here changes existing code, data, or prompts on its own.

## Contents

- Goal
- Minimum planability
  - The gate
  - Time-sufficiency
  - Current State and Desired State
- Progression
- Plan
  - Adaptive depth
  - Structural axis
  - Temporal axis (Time)
- Feedback and Replanning
- Presentation
- Relationship to Vision
- Open questions

## Goal

**Fact.** A Goal is the stable, persistent unit of "what the user wants to achieve" — identified by `goal_id`, its current truth always its latest history record (see [[03-architecture]] § Planning, [[04-current-state]]). This document doesn't redefine Goal; it only asks what has to be true about a Goal before "Plan" can mean anything.

Fulfilling a Goal means bridging it to something concrete happening in the world. That bridge is Plan — but before a Plan can be built at all, the agent needs enough information to build it responsibly. That gate is Minimum Planability, below.

## Minimum planability

**Hypothesis.** Before a Plan can be produced, the agent needs enough information to do so responsibly — not a fixed form the user must fill in, but a gate the agent checks per Goal.

### The gate

For anything a plan might need to know, three states apply:

```text
KNOWN                          → use it
UNKNOWN, and NECESSARY         → ask
UNKNOWN, but reasonably        → propose a default, let the user
suggestible                      confirm or adjust
```

The third case is a distinct move from either of the other two — not asking blankly, and not silently assuming.

**KNOWN** covers two different sources, not only what this conversation has stated: information the user has explicitly given, and reliable general/background knowledge the agent already has access to (how coffee is typically made, how habits typically form). It never covers anything personal to this specific user that hasn't been stated — a preference, a resource, a constraint, or a personal limitation stays UNKNOWN until the user says otherwise, no matter how common that preference might generally be.

This generalizes something already built: `generate_plan()` already refuses to plan a Goal that's too vague in content, asking a clarifying question instead (`backend/goals/plan/planner.py`; see [[03-architecture]] § Planning). The idea here is that the same gate should also cover *time* and, where relevant, *state* — not only vagueness of content.

### Time-sufficiency

**Hypothesis**, building on an existing **fact**. Does a workable timeframe exist for this Goal? Today, a duration phrase found in the Goal's own text resolves this deterministically (`extract_duration_phrase()`); its absence already triggers a clarifying question. What isn't yet handled: an open-ended, lifestyle-shaped Goal ("start training") has no natural end date at all, and a blank "how long?" doesn't fit it well — proposing a concrete, clearly labeled timeframe ("if you start this week, establishing a routine in about 8 weeks is realistic — use that?") fits the propose-and-confirm move above better than either asking or assuming.

### Current State and Desired State

**Hypothesis.** These are not a separate concept to elicit for every Goal — they are one instance of the gate above, applied to *state* rather than *time*. They earn an explicit place only when they say something the Goal's own wording doesn't already say, and that the agent can't safely guess.

Test: can Desired State be phrased independently of the Goal's own words, as an external, checkable fact? "Reach Silver" / "Silver" passes — the rank is a fact external to the phrasing. "Start training" / "I train regularly" fails — the second is a restatement of the first, not new information. Where the test fails, Current/Desired State should not be forced into the model as explicit, elicited concepts; the Goal's own text already carries what's needed. Where it passes, Current State should be *asked*, never assumed — the agent has no way to know a specific person's rank, page count, or measurement on its own.

Capacity (how much time/effort the user can realistically give this per period) and hard external constraints are further candidate instances of the same gate. Neither is developed further here — see Open Questions.

## Progression

**Hypothesis.** Progression is the movement from where a Goal currently stands toward it being fulfilled. Where Current State and Desired State exist (above), Progression has two distinct, named parts:

```text
Current State
      ↓
     Gap          — the difference: what's missing between Current and Desired
      ↓
Progression        — the movement through that gap
      ↓
Desired State
```

**Gap** names *what's missing* — a static comparison. **Progression** names *the movement across it* — what a Plan actually does. They are related but not the same thing.

Where no Current/Desired State exists (most habit/lifestyle Goals), Progression is understood more loosely: movement from having stated the intention toward having fulfilled it, with no named Gap to measure against. Progression does not require an explicit Gap to exist — it is the more general of the two concepts.

Where Progression happens to be quantifiable — a page count against a reading rate, a session count against a weekly frequency — the relationship between Current State, Desired State, Progression, Time, and Capacity can be made explicit and computable rather than left to prose (see [[03-architecture]] § Math). Most Goals' Progression is not quantifiable this way, and nothing here requires it to be.

## Plan

**Hypothesis.** A Plan is the agent's current, revisable understanding of how a Goal's Progression actually happens — expressed at whatever depth of structure that Progression actually needs, never more.

A Plan is not a static output. It is expected to change as Feedback arrives — revisability is part of what makes something a Plan, not a separate behavior added on afterward (see Feedback and Replanning, below).

**What distinguishes a Plan from a bare list of Actions:** a list of Actions carries no account of *why* these actions, in this order, actually constitute progress toward the Goal. A Plan carries that account — even when, for a small Goal, the account collapses to almost nothing ("the obvious next thing to do is X").

A Plan is expressed along two independent axes, below: a **structural axis** (what needs to happen) and a **temporal axis** (when).

### Adaptive depth

**Hypothesis.** Nothing below Action is mandatory. Depth is not chosen upfront as "how many levels does this Goal need" — it falls out of asking, at each level, one more basic question: **is this element already at a granularity where it can be acted on, or is it still too coarse to be a meaningful next unit?** The agent keeps decomposing only while the answer is "still too coarse," never as a separate, prior decision about how deep the whole Goal should go. This is why depth can differ across *different branches of the same Goal*, not only across different Goals — granularity is judged locally, per element, not globally, per Goal.

### Structural axis

**Hypothesis, terminology provisional** — see Open Questions.

```text
Goal
  └─ (0 or more) Stage   — a named, meaningful grouping of related Actions
        └─ (1 or more) Action   — a concrete thing to do
              └─ (0 or more) Micro-step   — friction-reducing sub-moves of ONE Action
```

- **Action** is the minimal valid Plan on its own — `Goal → Action`, with no Stage at all, is a complete, legitimate plan for a simple Goal.
- **Stage** groups several Actions that belong together — a Stage is not one Action, and one Stage can (and often does) hold more than one. Worked example: painting a house might have a "prepare surfaces" Stage containing wash/scrape/repair/prime as four separate Actions, and a "paint" Stage containing first-coat/second-coat as two more — different Actions can warrant different depth even within the same Goal (prepping might need Micro-steps for someone unfamiliar with the tools; painting might not).
- **Micro-step** exists only when one specific Action has real friction between deciding and starting it (packing a gym bag before a workout) — not a mechanical subdivision of time, and not needed for most Actions.

A grouping only earns the name Stage when it has real internal cohesion — Actions that belong together because they serve the same part of the Progression, not because they merely happen to occur one after another. A Stage is a meaningful segment of the path, not an arbitrary bundle of sequential Actions.

### Temporal axis (Time)

The underlying mechanism is **fact**; keeping it separate from the structural axis is a **decision**.

`year → month → week → today → now` is already built (`PLAN_KEYS`, the temporal-understanding Faculty — see [[03-architecture]] § Time). It answers *when*, describing the same Goal at different distances in time.

**Time is a dimension through which a Plan is organized and interpreted, not a level in the planning hierarchy.** A Stage is not a time slot, and a time horizon is not a Stage — the two axes may be loosely cross-referenced (a Stage might roughly target a given week), but neither is expressed in terms of the other.

## Feedback and Replanning

**Hypothesis.** Feedback's job is to update the understanding a Plan already holds — which Stage is current, whether Progression is happening — not to trigger a disconnected, from-scratch regeneration.

```text
Action → reality → Feedback → updated understanding → Replanning → revised Plan
```

**Hypothesis, open area.** Feedback is not the only reason Plan's understanding might need to change. Time passing can, by itself, change the planning situation — an approaching deadline makes the same Progression harder to complete in the time left, even if nothing the user did or reported has changed. This is conceptually distinct from Feedback: Feedback is information about what actually happened; a time-driven change is information about how much room is left to act, independent of any reported outcome. Whether and how the agent should notice this on its own is left open here — no mechanism is proposed.

**Limitation (confirmed).** Today, `apply_feedback()`'s ordinary outcome path calls `replan()`, which regenerates the temporal axis from a single fresh model call over the Goal's full history and does not touch the structural axis at all — a Goal's step list does not survive this path (`backend/goals/plan/planner.py`). Whether and how to change this is left open here, not decided.

## Presentation

**Hypothesis, deliberately separate from the model above.** Internal planning complexity is not the same thing as interface complexity — a Goal with a deep structural axis does not require a user to see every Stage/Action/Micro-step at once. Progressive disclosure, appropriate grouping, and how much of the model surfaces in the UI are presentation questions, downstream of this document, not part of the planning model itself.

## Relationship to Vision

Vision sits above this entire model, providing optional shared context across Goals — it does not participate in how any single Goal's Plan is built. See [[03-architecture]] § Vision.

## Open questions

- Is `Stage` one concept, or does it hide two distinct ones — a sequential **Phase** (ordered work segments, as in the paint example) and a checkable **Milestone** (a skill/state marker, as in a rank-climbing goal) — that deserve separate names?
- Can a Stage nest other Stages, for a sufficiently large Goal? Not decided either way.
- Does `Micro-step` need a name distinct from the prototype's existing `steps` field, or does `steps` simply need to be redefined to mean this?
- How far should Capacity and hard external constraints be developed as their own named instances of Minimum Planability's gate, versus staying implicit?
- Should a Plan's "current understanding" (current Stage, Progression status) ever become a small, persisted field carried forward across replans — the way `frozen_duration`/`current_step`/`vision_id` already are — or should it remain purely a matter of how the replan prompt reasons, with nothing new stored?

## See also

- [[03-architecture]] § Planning, § Time, § Math
- [[04-current-state]]
- `architecture_foundation/goals/plan/README.md` — flags the same Plan/Action data-model question this document explores conceptually
