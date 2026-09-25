# Architecture

What the components are, why they're split the way they are, and how they
connect. See `COMPONENT_MAP.md` for the reference table and `DECISIONS.md`
for what's actually settled vs. open.

## Two axes, kept deliberately separate

**Architecture components** are system responsibilities - what part of the
problem a piece of the agent owns. **Mechanisms** are how a component's job
might actually be done - a specific technology or technique.

A neural network, RAG, and embeddings are mechanisms, not components. None
of them gets a folder here. Where a mechanism might eventually matter, the
relevant component's `README.md` says so in prose - see `COMPONENT_MAP.md`'s
"Where mechanisms plug in" section for the full list. The reason this
matters: a component's responsibility should stay stable even if the
mechanism behind it changes completely (deterministic filtering today,
embeddings tomorrow, without the surrounding architecture needing to move).

## The operational loop: Vision → Goal → Plan → Action → Feedback

```text
Vision
 ↓
provides optional context to multiple Goals

Goal
 ↓
Plan
 ↓
Action
 ↓
Feedback
 ↺ (back into Plan, via replanning)
```

- **Vision** - why; the user's broader direction. Optional, and spans
  multiple Goals. Not a step in the loop below it - it sits above.
- **Goal** - what the user wants to achieve. A stable identity.
- **Plan** - how one specific Goal should be pursued.
- **Action** - what the user does right now. The narrowest slice of Plan.
- **Feedback** - what actually happened, closing the loop back into Plan.

All five are proven in the prototype (see `vision/`, `goals/goal/`,
`goals/plan/`, `goals/action/`, `goals/feedback/` for the specifics and the
reference files). This skeleton keeps them as five distinct responsibilities
even though the prototype's own data model currently merges Plan and Action
into one object - see `goals/plan/README.md` and `goals/action/README.md`
for why that's flagged as worth separating properly, not copied as-is.

## The wider loop

```text
USER
 ↓
CONVERSATION / INTERFACE
 ↓
INTERPRETATION / PARSING          (deterministic where possible - "recognize
 ↓                                 what you can name, admit what you can't")
MEMORY                             (raw history; "current state" is just the
 ↓                    ↘             latest view into it, not a separate store)
 ↓               USER REPRESENTATION   (derived, adaptive, exploratory)
 ↓                    ↙
REASONING / PLANNING              (LLM + deterministic rules, informed by
 ↓                                 both Memory and User Representation)
DECISION                          (today: deterministic routing. Later:
 ↓                                 + an intervention policy)
ACTION (user's next step)  /  EXECUTION (agent's own real-world action, future)
 ↓
FEEDBACK
 ↓
MEMORY (updated) ↺
```

Two corrections to the intuitive version of this flow, made explicit because
they weren't obvious until checked against the prototype's actual code:

- **"State" isn't a separate store from Memory.** In the prototype, the
  current state of a goal is just its most recent record
  (`get_latest_for_project()`) - a view into Memory, not something stored
  independently. Modeling it as its own component would introduce a
  distinction that doesn't exist in practice.
- **User Representation isn't only consulted after Reasoning/Planning.** It
  should be able to inform Reasoning/Planning directly (e.g. shaping how a
  replan is worded), not only feed a Decision made after the fact.

## Two different meanings of "Action" - resolved

"Action" is used two ways in earlier discussion of this project: the user's
immediate next step (part of the Vision→Goal→Plan→Action→Feedback loop,
already an established, working concept - see `goals/action/`), and the
agent performing something in the real world (creating a file, calling an
API - unbuilt, previously called "Acting" in the prototype's own docs). This
skeleton keeps them as two separate components with two separate names:
**Action** (the user's step, part of the core loop) and **Execution** (the
agent's own capability, see `execution/`) - reusing "Action" for both would
recreate exactly the naming drift already resolved once for
Action/Task/`right_now` in the prototype.

## Memory vs. Knowledge vs. User Representation

Three things that could all superficially be called "what the agent knows,"
kept separate because they answer different questions and come from
different sources:

- **Memory** - what has this agent's own operation actually recorded
  happening (goals, plans, feedback, actions)? Raw, first-party, the source
  of truth.
- **Knowledge** - what has the *user* supplied as external material (their
  own documents/notes)? A completely different corpus and purpose.
- **User Representation** - what has been *generalized* from Memory into an
  updated, compact belief about this user's patterns? Always derived and
  reconstructable from Memory, never a replacement for it, and never built
  from Knowledge.

## Where the LLM fits

The LLM is a mechanism inside **Reasoning** - never its own component. Every
call to a model, regardless of which component needs it (Plan and Feedback
today; potentially Decision or Knowledge later), goes through this one boundary, so
the provider stays swappable and prompt-construction/response-validation
logic isn't duplicated per component. See `reasoning/README.md`.

## Where RAG/embeddings fit

Not a component - a possible mechanism for two *different* retrieval needs
that shouldn't be assumed to share a solution:

- **Memory retrieval** - the agent's own history. Deterministic filtering
  (by goal, date, keyword) is likely sufficient for a long time; embeddings
  are a later upgrade only if filtering demonstrably isn't enough.
- **Knowledge retrieval** - user-supplied documents. More heterogeneous by
  nature; the prototype's own sketch already anticipates needing real
  retrieval here eventually (see `knowledge/README.md`).

## Where a Neural Network fits

Only as a possible future mechanism inside **User Representation** - and
only once there's enough real personal-scale history, and enough distinct
tracked patterns, that shared representation learning would actually pay
for itself over simpler statistics (an exponential moving average, a
Bayesian update). Never its own component. See `user_model/README.md`.
