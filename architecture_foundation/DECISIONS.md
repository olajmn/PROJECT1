# Decisions

What's actually been decided, vs. what's current fact, exploratory,
future, or genuinely unknown. Deliberately not padded with decisions that
haven't actually been made - an empty-looking category below is the honest
state, not a gap to fill in for its own sake.

**Tags:**
- **Decided** - an actual choice was made, with alternatives considered.
- **Current** - true today, in the prototype, not a choice being announced.
- **Exploratory** - a hypothesis, genuinely uncertain whether it becomes real.
- **Future** - a known, named need, not yet designed or decided how to meet.
- **Unknown** - an open question, deliberately not resolved yet.

## Decided

- **Vision is a separate, lightweight id+text store with an optional
  reference from Goal - not duplicated free text, not a relational
  hierarchy.** Made in the prototype (see its `docs/05-decisions.md` #17).
  Carried into this skeleton unchanged - `vision/README.md` documents it as
  settled, not re-opened here.
- **Architecture components and implementation mechanisms are kept
  strictly separate.** A neural network, RAG, and embeddings are never
  folders - see `ARCHITECTURE.md` and `COMPONENT_MAP.md`'s "Explicitly not
  components" section.
- **"Action" (the user's next step) and "Execution" (the agent's own
  real-world action) are two different components with two different
  names.** Reusing one word for both was rejected specifically to avoid
  recreating the Action/Task/`right_now` naming drift already resolved once
  in the prototype.
- **Expectation/Discrepancy is not a component separate from User
  Representation.** It's the operation User Representation performs, not
  a second responsibility.

## Current (true today, in the prototype)

- Vision, Goal, Plan, Action, and Feedback all work end to end - see each
  one's own `README.md` for the reference file.
- Temporal understanding is the one proven Faculty (deterministic duration/
  timeframe interpretation) - see `foundation/README.md`.
- Persistence (local JSON, atomic writes) works and is the only storage
  mechanism in use - see `infrastructure/README.md`.
- The interface is a local Flask/Jinja devtool, not a designed product
  frontend - see `interface/README.md`.
- Plan and Action are the same data structure and the same LLM call in the
  prototype's actual code, even though this skeleton models them as two
  components - see `goals/plan/README.md`.

## Exploratory (genuinely uncertain, may not be built)

- User Representation / adaptive user model at all - see `user_model/README.md`.
- A proactive intervention policy (the agent saying something unprompted) -
  see `decision/README.md`.
- A minimal visual identity for the agent - see `interface/visual_identity/README.md`.
- The "relational continuity" product hypothesis (that continuity,
  specificity, and consistent identity - not simulated emotion - could make
  the agent feel like "mine" over time) - a design/product hypothesis, not
  a technical component; see `interface/visual_identity/README.md` and
  `user_model/README.md` for where it would touch actual architecture.
- Whether a neural network is ever the right mechanism for User
  Representation (current position: no, not until simpler statistics prove
  insufficient at real usage scale).
- Time/cadence as a dimension of the agent's own behavior - how often it
  follows up, cooldown between interventions, expected cadence, shaped by
  user preference - not just deadline/duration metadata on a Goal. Touches
  `foundation/README.md` (the Time Faculty), `decision/README.md`
  (intervention policy's cooldown), and `user_model/README.md`, without
  being owned by any one of them. Referred to loosely as the agent's
  "personality" in this sense - behavior over time, not tone or a
  simulated persona; distinct from, and not to be confused with,
  `interface/visual_identity/README.md`'s explicit rejection of simulated
  personality/emotion. Raised 2026-08-31, not designed.

## Future (named, not yet designed)

- Memory as its own real capability (not just unused raw JSON).
- Knowledge / retrieval over user-supplied material.
- Execution - the agent performing real actions in the world, likely by
  delegating to an existing external runtime rather than building one from
  scratch (a direction raised, not decided - see `execution/README.md`).
- Conversation as its own domain, independent of a specific Goal's thread.
- World - live external data (weather, calendar, etc.) - a deliberate
  empty placeholder, unchanged from the prototype.

## Unknown (deliberately open)

- Whether Vision should ever be editable/deletable, or stays create-only.
- Whether/how a Goal's Vision ever gets summarized into the LLM's context
  when planning or replanning.
- Whether Memory retrieval ever needs more than deterministic filtering.
- Which mechanism (EMA, Bayesian, something else) User Representation
  would actually start with, if built.
- Whether Decision's future intervention policy is worth building at all,
  versus staying purely reactive indefinitely.
- Whether Execution is built at all, or the agent stays reasoning-only
  long-term.
