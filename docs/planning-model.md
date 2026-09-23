# Planning Model

> Working conceptual model for what a Goal's plan actually means in this agent — not a technical specification, a data model, or a system prompt. Concepts below are labeled **fact** (confirmed in the running prototype), **hypothesis** (a working idea, not yet decided), **limitation** (a confirmed gap in current behavior), or **open question** (deliberately unresolved) — the same taxonomy as `global-standards/DOCUMENTATION_STYLE_GUIDE.md` §5. Most of what follows is hypothesis: this document exists to give planning a shared vocabulary to reason with, not to record a settled architecture. Nothing here changes existing code, data, or prompts on its own.

> **Read today:** capability name = **Project**; structural / WHAT axis = **canvas** (`project/panes/canvas/`); Stage 3 = **engine/judgment/** (`decide`, `run_stage3`, …); calendar dual = **engine/time/calendar.py**; revise = `engine/reason.py` (`replan` / `apply_new_duration`). Wire identity = `project_id` (deprecated `goal_id` mirror — #29). Full label map: [[04-current-state]] § Vocabulary, [[05-decisions]] #28. This file still says Goal/Plan where that is the conceptual vocabulary.

## Contents

- Goal
- Minimum planability
  - The gate
  - ASK vs. SUGGEST
  - Interpreting a response to ASK/SUGGEST
  - Time-sufficiency
  - Current State and Desired State
- Progression
- Plan
  - Adaptive depth
  - Structural axis
  - Action
  - Decomposition / zoom
  - Temporal axis (Time)
- Feedback and Replanning
- Reality, Observation, and Verification
  - Completion
- Conversation
- Presentation
- Relationship to Vision
- Open questions

## Goal

**Fact.** A Goal (product: **Project**) is the stable, persistent unit of "what the user wants to achieve" — identified by `project_id` on the wire (legacy field/param name `goal_id` still appears in Python and as a deprecated API mirror — see [[05-decisions]] #29); its current truth is always its latest history record (see [[03-architecture]] § Planning, [[04-current-state]]). This document doesn't redefine Goal; it only asks what has to be true about a Goal before "Plan" can mean anything.

Fulfilling a Goal means bridging it to something concrete happening in the world. That bridge is Plan — and at each point the agent is about to commit to something more concrete (a first Action, a Plan, a deeper level of a Step), it needs enough understanding to do so responsibly. That assessment is Minimum Planability, below.

**Fact.** Vision is optional background context, not a precondition for a Goal to be planned at all — both `Goal → Plan → Action` and `Vision → Goal → Plan → Action` are complete, valid shapes (see § Relationship to Vision).

## Minimum planability

**Hypothesis, revised 2026-09-08.** Minimum Planability is not a one-time gate a Goal passes before planning can begin, and not a checklist of fields — Current State, Desired State, Time, Capacity, Constraints, and so on — that must all be filled in before anything can happen. It is a **local, recurring assessment**: does the agent have enough understanding to responsibly commit to the specific thing it is about to produce or do right now — the next Action, the next level of a Step's decomposition, the next horizon of a Plan — not the Goal's whole eventual resolution at once. Different Goals need different information to reach that bar; the same Goal can need different information at different levels of planning, as understanding deepens.

**The necessity test.** An unknown becomes necessary exactly when the output the agent is about to produce would be different, invalid, or presumptive depending on what that unknown turns out to be. If the intended next output stays the same, safe, and non-presumptuous regardless of the unknown's actual value, resolving it can wait until planning actually reaches a level that depends on it — it does not need to be resolved just because it could, in principle, matter eventually. This is a semantic judgment made about a specific case, not a mechanical algorithm.

Several unknowns can exist at once, each evaluated against whatever concrete commitment it actually blocks, not against the Goal as a whole. A Plan does not require every eventually-relevant unknown to close before it can exist, and the agent does not need complete or perfect information to begin planning — it produces what today's understanding safely supports, and lets unknowns that only matter at a deeper level surface and resolve as planning actually reaches that level (see Adaptive depth, below, for the same underlying principle applied to structure rather than information).

### The gate

For any specific unknown the agent is currently weighing, three states apply:

```text
KNOWN                          → use it
UNKNOWN, and NECESSARY         → ask
UNKNOWN, but reasonably        → propose a default, let the user
suggestible                      confirm or adjust
```

The third case is a distinct move from either of the other two — not asking blankly, and not silently assuming.

**KNOWN** covers two different sources, not only what this conversation has stated: information the user has explicitly given, and reliable general/background knowledge the agent already has access to (how coffee is typically made, how habits typically form). It never covers anything personal to this specific user that hasn't been stated — a preference, a resource, a constraint, or a personal limitation stays UNKNOWN until the user says otherwise, no matter how common that preference might generally be.

This generalizes something already built: `generate_plan()` already refuses to plan a Goal that's too vague in content, asking a clarifying question instead (`backend/goals/plan/planner.py`; see [[03-architecture]] § Planning). The same three-way distinction applies wherever the necessity test above is met — content, time, state, or any other unknown a deeper level of planning turns out to need — not only at Goal creation. See ASK vs. SUGGEST, below, for what the third state actually means.

### ASK vs. SUGGEST

**Hypothesis, added 2026-09-08.** ASK and SUGGEST both respond to an UNKNOWN, but differ in whether the agent contributes any content toward the answer:

> ASK identifies something that must come from the user when the agent has no legitimate content to contribute toward the answer.
>
> SUGGEST allows the agent to contribute generic, non-personal, provisional structure that creates progress or reduces uncertainty without pretending to know the user's personal answer.

ASK contributes nothing — it names the missing piece and stops, because the answer belongs to the user (a preference, a resource, a constraint, a personal fact not yet stated) and no general reasoning gets meaningfully closer to it. SUGGEST contributes something — a value, a narrowed set of options, a small starting move — grounded only in generic, non-personal reasoning, and always held open for the user to confirm or adjust rather than treated as settled.

A useful test for whether a candidate SUGGEST is actually generic: would it remain reasonable across plausible alternative explanations for why the user has the Goal? A suggestion that only holds up under one particular unstated motivation (e.g. treating career as the reason someone wants to move to a new city, when family, cost, climate, or lifestyle are equally plausible) was relying on a personal assumption dressed as generic advice.

The same distinction separates SUGGEST from Plan:

> PLAN begins when the agent has sufficient understanding to treat its current understanding as the working basis for a plan, without requiring a basic premise to be confirmed first.

A SUGGEST's content carries its own unconfirmed premise — "is this even the right starting point?" — until the user accepts or adjusts it; a Plan carries no such premise. It is the agent's current best understanding, revisable only through ordinary Feedback and Replanning (see below), not through a "did you actually mean this" check. Confirming a SUGGEST is the moment it becomes something a Plan can be built on — this is already how `suggested_duration` works (see Time-sufficiency, below).

Neither ASK nor SUGGEST is a level in `Goal → Step → Action`, and neither is a fixed, global status for a whole Goal. Both are ways the agent can respond to one specific, currently-relevant unknown (see The gate, above) — a Goal can simultaneously have one unknown resolved by SUGGEST, another still needing ASK, and a third not yet relevant at all.

**Illustrative expressions, not a closed taxonomy.** SUGGEST is not synonymous with "propose an Action" — `suggested_duration`, the one SUGGEST behavior actually built, proposes a value, not an Action, which already rules that reading out. What SUGGEST has taken as a shape, case by case, so far:

- a generic default value (e.g. a proposed timeframe)
- a convergent exploratory Action, when the unknown is Current State or "what to do first" and any reasonable direction converges on the same safe move
- a bounded set of directions or options, when the unknown is a genuine choice between structurally different paths and picking one for the user would invent a preference
- a self-exploratory activity, when the missing thing is personal but the user can more easily externalize it through a small activity than answer a blank question directly

These are examples of shapes SUGGEST has taken, not four formal types it must choose between. The boundary between the last two of these and ASK is genuinely unresolved, not just under-specified: a bounded menu ("diet / activity / sleep — which matters to you?") still requires the actual choice to come from the user, exactly like ASK, while also contributing generic structure, exactly like SUGGEST — both properties can be true of the same response at once (see Open questions).

### Interpreting a response to ASK/SUGGEST

**Hypothesis, added 2026-09-08.** ASK and SUGGEST have two roles, not one. The first is already covered above: they are the *output* of Minimum Planability's gate for one specific unknown. The second is not yet named: once the agent actually communicates an ASK or a SUGGEST, that contribution (`X`) becomes a **reference point** the user's next response (`Y`) can be interpreted against — not a demand that `Y` must answer `X` directly, only that `Y` should be read *in relation to* `X` where such a relation exists.

`Y`'s relation to `X` falls into one of three semantic relations — a way of thinking about what a response means, not a new entity, a stored field, or a runtime classifier:

- **Observation / Evidence** — `Y` supplies or corrects information relevant to the agent's understanding (a new fact, a correction, a clarification, a stated motivation). This is the same Observation/Evidence already defined in § Reality, Observation, and Verification, below — the only addition here is that it isn't exclusive to the post-execution case: it can arrive in response to an ASK/SUGGEST, before any Action has been attempted, not only after `Action → Reality`. "Correction" is not a separate concept from "new information" here — both update understanding the same way, differing only in whether they add to or overturn what the agent believed.
- **Directly supplied KNOWN** — `Y` turns something that was `UNKNOWN, suggestible` into `KNOWN` (see The gate, above). Accepting the agent's own proposal ("Yes") and replacing it with the user's own ("I'd rather start with my portfolio") are the same move at this level — both close the same open unknown, differing only in whose content the answer is. What the agent does with a directly-supplied KNOWN value next isn't specified here; if it's already concrete enough to serve as the next commitment, Minimum Planability's re-evaluation is immediate, otherwise it stays open a while longer.
- **No new information** — `Y` doesn't reduce the currently open unknown (a bare "No", an unrelated reply). This doesn't by itself mean the agent should repeat itself — only that this particular response gave it nothing new to work with.

`X` never fixes what `Y` must mean. A reply can introduce information the agent never asked for at all — "Start by researching some cities" answered with "I actually want to move because my family lives there" is Observation/Evidence about motivation, not an acceptance or rejection of the research suggestion. The relation is always established by reading `X` and `Y` together, never assumed from `X`'s own content alone.

The semantic sequence, independent of how any of it is eventually implemented:

```text
Minimum Planability
        ↓
ASK / SUGGEST (agent's contribution X)
        ↓
user's response (Y)
        ↓
Y interpreted relative to X
        ↓
updated understanding
        ↓
Minimum Planability, reassessed
        ↓
ASK / SUGGEST / PLAN
```

A response is always interpreted before the agent's next planning decision - that is the only thing asserted here. Whether that interpretation immediately produces a PLAN, another SUGGEST, or a real ASK depends entirely on what `Y` turned out to be, not on a fixed rule that answering an ASK/SUGGEST always leads to a new full planning pass.

This is a distinct, pre-commitment sibling to the post-execution loop in § Feedback and Replanning, below - both share the same underlying shape (a contribution, a response, an interpretation, an updated understanding, a reassessment), but operate on different material: this loop resolves what the agent has enough premise to commit to; the other resolves what actually happened once it did. Keeping them separate matters for the same reason confirming a SUGGEST is not the same as reporting an Action done (see above) - one precedes Reality, the other reports on it.

### Time-sufficiency

**Hypothesis**, building on an existing **fact**. Does a workable timeframe exist for this Goal? Today, a duration phrase found in the Goal's own text resolves this deterministically (`extract_duration_phrase()`); its absence already triggers a clarifying question. What isn't yet handled: an open-ended, lifestyle-shaped Goal ("start training") has no natural end date at all, and a blank "how long?" doesn't fit it well — proposing a concrete, clearly labeled timeframe ("if you start this week, establishing a routine in about 8 weeks is realistic — use that?") fits the propose-and-confirm move above better than either asking or assuming. This is the one SUGGEST behavior actually built and verified today (`suggested_duration`, `backend/goals/plan/planner.py`) — see ASK vs. SUGGEST, above, for the general form this is one instance of.

### Current State and Desired State

**Hypothesis.** These are not a separate concept to elicit for every Goal — they are one instance of the gate above, applied to *state* rather than *time*, and subject to the same necessity test (see above): they earn an explicit place only when the specific thing the agent is about to produce actually depends on them, not as a standing pair of fields for every Goal.

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

**What distinguishes a Plan from a bare list of Steps:** a list of Steps on their own carries no account of *why* these, in this order, actually constitute progress toward the Goal. A Plan carries that account — even when, for a small Goal, the account collapses to almost nothing ("the obvious next thing to do is X").

A Plan is expressed along two independent axes, below: a **structural axis** (what needs to happen) and a **temporal axis** (when).

### Adaptive depth

**Hypothesis.** No fixed decomposition depth is mandatory. Depth is not chosen upfront as "how many levels does this Goal need" — it falls out of asking, at each level, one more basic question: **is this Step already at a resolution where an Action can be projected from it, or is it still too coarse to be a meaningful next unit?** The agent keeps decomposing only while the answer is "still too coarse" (see Decomposition / zoom, below), never as a separate, prior decision about how deep the whole Goal should go. This is why depth can differ across *different branches of the same Goal*, not only across different Goals — granularity is judged locally, per Step, not globally, per Goal.

Minimum Planability (above) and adaptive planning depth apply the same broader principle at different dimensions: resolve only what is necessary at the current level of planning. Minimum Planability governs *informational* sufficiency — does the agent know enough to responsibly produce what it's about to produce; adaptive depth governs *structural* resolution — is a Step already fine-grained enough to project an Action from. They stay separate concepts, each judged on its own terms, and resolving one does not resolve the other — but neither is decided once, upfront, for the whole Goal; both are local, recurring judgments made at whatever point planning tries to go one level deeper.

### Structural axis

**Hypothesis, terminology refined 2026-09-07** — see Open Questions. Earlier drafts of this document described a fixed three-level hierarchy (`Goal → Stage → Action → Micro-step`), with "Action" as the atomic structural unit. That framing is superseded by a single, relative concept:

**Step** is not a global, fixed size — it is whatever grouping the current Plan needs, at whatever resolution it's currently understood at. The same wording can be a Goal, a Step, or an Action depending on where it sits in one specific Plan and how much resolution that Plan currently needs there — not a property of the text itself. Worked example:

```text
Goal: Build a good life
  Step: Education
    Step: Master's degree
      Step: Semester
        Step: Course
          Step: Assignment
            Action: Open the document and write the first paragraph
```

Nothing here requires this whole chain to exist at once (see Decomposition / zoom, below) — it illustrates relative resolution, not a taxonomy every Goal must be sorted into.

- **Step** is the general term for a node on this axis — a claim about a state or change in Reality that the Plan needs realized (see Reality, Observation, and Verification, below). A Step is the minimal valid Plan on its own — `Goal → Step`, with no further decomposition, is a complete, legitimate plan for a simple Goal.
- **Action** is never a Step itself — it is the operative thing done to move a Step toward Reality (see § Action, below).
- What earlier drafts called **Stage** (a grouping of related Actions with real internal cohesion) and **Micro-step** (friction-reducing sub-moves of one Action) are not abandoned concepts — they describe what a *coarse* Step and a *very fine* Step, respectively, look like under this relative model, rather than two additional fixed levels of their own. Whether they still deserve separate names is open (see Open Questions).

### Action

**Hypothesis.** Action is a concrete operation — undertaken by the human, the agent, or (not built, see Open Questions) the agent via a tool or system — that investigates, influences, or changes Reality in the direction of realizing a Step. Unlike a Step, an Action is not necessarily a permanent, persisted element of the Plan: it can be a **situational projection** of whatever Step currently needs attention, generated when it's needed rather than stored upfront.

This is why an Action can be purely investigative (checking whether a Step is already true) as well as world-changing (doing something to make it true) — both serve the same purpose: producing information or change relevant to a Step's claim (see Reality, Observation, and Verification, below).

The agent can, in principle, ask the same recursive question at any point it meets friction or missing understanding: *what has to happen for this to move forward?* — and answer it at increasing resolution until it reaches something that can actually be done right now. That recursive move is Decomposition / zoom, below.

### Decomposition / zoom

**Hypothesis.** Decomposition is not a requirement that a Step's entire sub-tree be built up front. More precisely:

> Decomposition is a mechanism for increasing the resolution of the agent's understanding of one point in the Plan, when that's actually needed — not a permanent, mandatory tree.

The original Step keeps its identity even as the agent's understanding of what has to happen under it becomes more detailed. Zooming into "Find a gym" to reason about "search alternatives → pick one → sign up" doesn't retire "Find a gym" as the thing that ultimately needs to be resolved (see Completion, below) — the finer content exists to inform the next Action, not to replace the Step it's zooming into.

Deliberately left open here, not decided: whether this finer content is ever persisted, and if so, as a container, a tree, a replacement, or something read alongside the original Step (see Open Questions). This document only commits to the resolution-increase framing, not a data shape.

### Temporal axis (Time)

The underlying mechanism is **fact**; keeping it separate from the structural axis is a **decision**.

`year → month → week → today → now` is already built (`PLAN_KEYS`, the temporal-understanding Faculty — see [[03-architecture]] § Time). It answers *when*, describing the same Goal at different distances in time.

**Time is a dimension through which a Plan is organized and interpreted, not a level in the planning hierarchy.** A Step is not a time slot, and a time horizon is not a Step — the two axes may be loosely cross-referenced (a Step might roughly target a given week), but neither is expressed in terms of the other.

## Feedback and Replanning

This is the post-execution sibling of § Interpreting a response to ASK/SUGGEST, above - same underlying shape (a contribution, a response, an updated understanding, a reassessment), applied after something has actually been attempted in the world rather than before a commitment is made. See that section for why the two are kept conceptually separate rather than merged into one general mechanism.

**Hypothesis.** Feedback's job is to update the understanding a Plan already holds — which Step is current, whether Progression is happening — not to trigger a disconnected, from-scratch regeneration. Replanning means updating that understanding in light of new information; it does not inherently mean regenerating the whole Plan from nothing, even though that happens to be how today's `replan()` treats the temporal axis (see Limitation, below).

```text
Action → Reality → Observation/Feedback → Verify → updated understanding → Replanning → revised Plan
```

See Reality, Observation, and Verification, below, for what sits between Feedback arriving and understanding actually changing.

**Hypothesis, open area.** Feedback is not the only reason Plan's understanding might need to change. Time passing can, by itself, change the planning situation — an approaching deadline makes the same Progression harder to complete in the time left, even if nothing the user did or reported has changed. This is conceptually distinct from Feedback: Feedback is information about what actually happened; a time-driven change is information about how much room is left to act, independent of any reported outcome. Whether and how the agent should notice this on its own is left open here — no mechanism is proposed.

**Limitation (confirmed).** Today, `apply_feedback()`'s ordinary outcome path calls `replan()`, which regenerates the temporal axis from a single fresh model call over the Goal's full history and does not touch the structural axis at all — a Goal's step list does not survive this path as *content* (`backend/goals/plan/planner.py`). Whether and how to change this is left open here, not decided. This is distinct from Step *completion*, which is now handled separately — see Completion, below.

**Fact (2026-09-07).** A related but separate integrity issue was found and fixed the same day this was implemented: two of `apply_feedback()`'s branches (`goal_completed`, `action_in_progress`) saved a new record without carrying `current_step`/`step_status` forward, silently resetting a Goal's step progress to its defaults on an ordinary check-in message. Fixed by passing both through unchanged, verified against a Goal sitting mid-way through its step list. This was a state-preservation bug in the implementation, not a gap in this conceptual model.

## Reality, Observation, and Verification

**Hypothesis.** A Step is a claim about a state or change in Reality — "a suitable gym has been found," "the components have been acquired." Three things are conceptually distinct here, even though today's prototype has only one channel for the second and folds the third into ordinary feedback handling:

- **Reality** — what is actually true in the world, independent of anyone's knowledge of it.
- **Observation / Evidence** — the information the agent actually receives about Reality. In this prototype, today, this is exclusively human self-report; an agent operating more autonomously would eventually also draw on tool calls or system observations (not built, see Open Questions).
- **Understanding** — the agent's current, held belief about the situation, which Observation/Evidence is used to update.

**Verification** is the (today informal, internal) judgment of whether the available Observation/Evidence gives grounds to say a Step's claim now holds. A `TRUE` / `FALSE` / `UNKNOWN` framing is a useful way to *think* about this — self-report is evidence toward an answer, not the answer by definition — but this document does not commit to it as a stored field, a confidence score, or an evidence-object schema. Whether verification ever needs to become an explicit, separately-named phase in the control flow (rather than an implicit decision folded into feedback handling) is left open — see Open Questions.

### Completion

**Hypothesis.** Step completion is the conclusion that a Step's claim is realized — reached through Verification, not merely inferred from an Action having been attempted. This is a materially different criterion from "an Action was reported done": searching for a gym (Action) is not the same claim as having found and chosen one (Step) — see § Action, above.

**Fact (2026-09-07, prototype).** A minimal version of this distinction — Design A — is implemented: each Step carries an `open`/`resolved` status, separate from `current_step`. An Action can be reported done without its Step becoming resolved; a Step is only marked resolved through an explicit, structured signal (never inferred from free text), and `current_step` only advances when that happens. This is a narrow, structural fix for one specific gap, not an implementation of the fuller Reality/Observation/Verification model above — there is no evidence list, no confidence, and no autonomous verification behind it. See `backend/goals/plan/planner.py`'s `advance_step()`.

**Open, deliberately not solved by the above.** For a habit- or process-shaped Step ("establish a training routine"), the relevant claim is a pattern sustained over time, not a single point-in-time fact — what counts as sufficient Observation/Evidence for that kind of Step is left entirely open here. The `open`/`resolved` fact above does not resolve this; it only gives such a Step somewhere to eventually record a judgment, whenever and however that judgment gets made.

## Conversation

**Limitation (confirmed, observed 2026-09-07).** Live testing surfaced a concrete gap between this document's model and Conversation's actual behavior. Goal: *"I want to get my job search organized and get a job in development."* The agent asked: *"What specific tasks or steps will be taken to get the job search organized?"* The user answered explicitly: *"I don't know exactly yet. That's what I want you to help me figure out."* The agent's next message asked, in substance, the same question again: *"What specific steps will you take to get your job search organized?"*

This is the transition Minimum Planability is meant to handle (see above) — `UNKNOWN, but reasonably suggestible → propose a default, let the user confirm or adjust` — but Conversation did not make it here: told the user doesn't know, it re-asked rather than reasoning about what's necessary and proposing something.

At the same time, the UI showed a concrete Action: *"Make a list of your current job search resources, including job boards, career websites and social media groups."* Some plan/Action-generation clearly did happen — it just wasn't surfaced constructively in the dialogue itself. The likely underlying cause is not diagnosed here, deliberately: this entry records the observation, not a fix.

**Principle, reaffirmed by this observation.** Internal planning/reasoning is not the same thing as user-facing conversation. That an Action was generated somewhere does not mean Conversation successfully expressed the agent's reasoning to the user — these are two different layers, and this gap is functional/model, not evidence that the underlying architecture needs restructuring.

## Presentation

**Hypothesis, deliberately separate from the model above.** Internal planning complexity is not the same thing as interface complexity — a Goal with a deep structural axis does not require a user to see every Step at once. Progressive disclosure, appropriate grouping, and how much of the model surfaces in the UI are presentation questions, downstream of this document, not part of the planning model itself. This is a distinct concern from Conversation's limitation above: that gap is about the agent's reasoning not reaching the dialogue at all, not about how much of an already-well-formed response should be shown at once.

**Plan is not the same thing as how it's communicated.** A Plan is part of the agent's internal model/state (see § Plan, above); chat, a list, cards, a timeline, or a more specialized Active Goal interface are different presentations of that same state, not different plans. Communicating a Plan as chat text today does not mean the underlying semantic model is chat-shaped — the same Plan could equally be rendered another way later without this document changing at all.

## Relationship to Vision

Vision sits above this entire model, providing optional shared context across Goals — it does not participate in how any single Goal's Plan is built. See [[03-architecture]] § Vision.

## Open questions

- What earlier drafts called `Stage` and `Milestone` are now understood as a coarse Step and a checkable, state-marker Step respectively (see § Structural axis) — but do they still deserve their own names for clarity, or is "Step at a given resolution" enough?
- What data shape (if any) should Decomposition/zoom persist — a container, a tree, a replacement of the original Step, or something read alongside it? Deliberately left open (see § Decomposition / zoom).
- How far should Capacity and hard external constraints be developed as their own named instances of Minimum Planability's gate, versus staying implicit?
- How the agent should judge whether a Goal's plausible directions converge on one safe starting move or genuinely fork into different, value-laden paths (see § ASK vs. SUGGEST) — used throughout that section's examples, never reduced to an operational test.
- The exact boundary between a bounded ASK and SUGGEST expressed as a bounded menu of options (see § ASK vs. SUGGEST) — both can be true of the same response at once; not decided whether this should stay an acknowledged overlap or resolve into something else.
- How a repeated SUGGEST should be bounded — a SUGGEST re-issued without any new Observation risks the same failure shape as a repeated ASK, just differently dressed.
- How several simultaneous unknowns should be composed operationally when more than one gates the same commitment at once — described here only by example (see § The gate), not by a rule.
- Whether SUGGEST's illustrative expressions (see § ASK vs. SUGGEST) ever need more explicit modeling, or stay expressed only as prose examples.
- Whether today's local model can actually make the ASK/SUGGEST/necessity judgments described above reliably enough to act on — a separate, model-limitation question this document deliberately doesn't assume an answer to either way.
- Should a Plan's "current understanding" (current Step, Progression status) ever become a small, persisted field carried forward across replans — the way `frozen_duration`/`current_step`/`vision_id`/`step_status` already are — or should it remain purely a matter of how the replan prompt reasons, with nothing new stored?
- Should Verification (see § Reality, Observation, and Verification) ever become an explicit, separately-named phase in the control flow, or does folding it implicitly into feedback handling stay adequate?
- What counts as sufficient Observation/Evidence for a habit- or process-shaped Step's completion? Deliberately unresolved (see § Completion).
- How would autonomous, tool- or system-based Observation ever be represented, if the agent starts acting more independently? Not needed while human self-report is the only channel.
- Whether the agent's need to track its own prior ASK/SUGGEST contribution (`X`) to interpret a reply (`Y`) is a narrow instance of a broader self-model/agent-continuity question — see [[03-architecture]]'s self-model hypothesis under § Long-Term Architecture — left as an open architectural hypothesis there, not decided or extended here.

## See also

- [[03-architecture]] § Planning, § Time, § Math
- [[04-current-state]]
- `architecture_foundation/goals/plan/README.md` — flags the same Plan/Action data-model question this document explores conceptually
