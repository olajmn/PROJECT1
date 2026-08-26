# 03 — Architecture

> How the agent is structured: what it's made of, how the pieces relate, and what principles guide how it grows. The map, not a master note — not the story of how this structure was reached (see [[06-development]]), not the reasoning behind a specific choice (see [[05-decisions]]), and not what's actually implemented right now (see [[04-current-state]]).

## 1. Architectural overview

### Diagram

See `03-architecture.drawio` in this folder — a visual map of the agent's architecture and its planned extensions. Green indicates built components; gray dashed elements are planned.

### Program

> The agent helps a person turn a goal into a concrete plan.

The architecture is organized around the progression from **goal → plan → action → feedback → replan**.

The conceptual model behind that progression, clarified 2026-08-26 (see [[06-development]]):

- **Vision** — why / the user's overall direction, optionally spanning multiple Goals. Not a pipeline stage.
- **Goal** — what the user wants to achieve. A stable identity.
- **Plan** — how one Goal should be pursued, across time horizons.
- **Action** — what the user does right now. The narrowest, most immediate horizon of Plan.
- **Feedback** — what actually happened, reported back by the user.

Vision sits above this loop, providing optional context; it does not sit inside it. See § Long-term architecture for what "above" means concretely, and for why Action/Task/`right_now`/"today's task" are the same concept under different names.

### Three architectural lenses

| Dimension     | Question                        | Examples                                      |
| ------------- | ------------------------------- | ---------------------------------------------- |
| **Domains**   | What does the system operate on? | Time, Goals, Planning, Conversation, Knowledge |
| **Faculties** | What can the agent understand or interpret? | Temporal understanding, Language, Semantics |
| **Pipeline**  | What happens, in what order?    | User → Reasoning → Planning → Action → Result |
| **Infrastructure** | What technical machinery supports the system? | Persistence, storage, external services |

These are complementary views of the same system rather than competing structures.

---

## 2. System structure

### Domains

A **Domain** is an area of responsibility or subject matter that the system operates on.

| Domain       | Responsibility                            |
| ------------ | ------------------------------------------ |
| Time         | Durations, timeframes, dates, deadlines   |
| Goals        | Define and manage user goals              |
| Planning     | Turn goals into plans and revise them     |
| Tasks        | Represent concrete actions                |
| Conversation | Interaction between user and agent        |
| History      | Preserve and retrieve past activity       |
| Knowledge    | Retrieve relevant user-provided knowledge |

`right_now` is currently represented inside the plan structure, but architecturally it should eventually represent an action or trigger rather than another time horizon.

### Faculties

A **Faculty** is a reusable area of agent understanding that is not tied to one Domain or one pipeline stage.

A Domain does not automatically get its own Faculty just because the agent needs to reason about it. Time, for example, is a Domain (what the system operates on); temporal understanding is the corresponding Faculty (the agent's reusable capability to interpret it - recognizing what "this weekend" means, comparing durations, etc.). Temporal understanding is the first established Faculty. Other candidates include Language and Semantics, but a Faculty should emerge through actual reuse across the system rather than being created purely as a conceptual category.

### Infrastructure

**Infrastructure** is shared technical machinery used by the system but which does not itself represent something the agent understands.

Persistence is the current example.

Infrastructure therefore differs from a Faculty:

> A Faculty understands something. Infrastructure moves, stores, or provides something.

### Pipeline

The Pipeline describes execution order:

```text
User → Reasoning → Planning → Action → Result
```

It is orthogonal to both Domains and Faculties.

A Domain describes **what the system operates on**.
A Faculty describes **what the agent understands**.
The Pipeline describes **what happens, and in what order**.

The Action stage is reasoning-only today - the agent doesn't yet perform external actions (creating a file, calling an API). Building that out is a parked idea: see [[06-development]] § Parking Lot.

---

## 3. Runtime architecture

```text
UI
 ↓
Backend
 ↓
Reasoning
 ↓
Planning / Action
 ↓
Persistence / External systems
 ↓
UI
```

The UI and backend are separate architectural layers. The current interface may change without requiring the agent's core logic to become tied to a particular frontend.

The backend is therefore treated as the durable core, while interfaces are replaceable clients.

---

## 4. Architectural principles

### 1. Local-first

The user's device remains the authoritative copy of their data.

### 2. Portable

User data should remain in open, human-readable formats where practical.

### 3. Replaceable infrastructure

Cloud services, synchronization servers and external APIs are dependencies, not the source of truth.

### 4. Privacy by architecture

Sensitive personal data should remain local where possible. If synchronization is introduced, it should preserve end-to-end encryption and user ownership.

### 5. Start simple

Do not introduce databases, vector stores, services or distributed infrastructure until the current implementation creates a real, felt need for them.

> The app should be able to disappear without the user's history disappearing.

See [[05-decisions]] for the reasoning behind specific architectural decisions.

---

## 5. Architectural components

### Time — Domain / Temporal understanding — Faculty

Time is a Domain (durations, timeframes, dates, deadlines); temporal understanding is the Faculty that provides deterministic interpretation of temporal expressions and durations.

It handles concepts such as:

* temporal expression matching
* duration resolution
* fixed goal timeframes
* relative duration comparison

Time interpretation is deliberately separated from LLM reasoning: **code decides, the model is told**.

Activity-specific interpretation of duration remains outside the established temporal-understanding Faculty for now.

### Planning — Domain

Planning turns a goal into a concrete sequence of time horizons and actions, and supports revision through feedback:

```text
Goal
 ↓
Plan
 ↓
Action
 ↓
Feedback
 ↓
Replan
```

See § Vision below for a concept above this pipeline, providing optional shared context for multiple Goals - distinct from Plan and not a new stage here.

### Vision — context shared across Goals

> Minimal representation implemented 2026-08-26 (see [[06-development]]). Naming and scope were exploratory before this date; both are now settled as described here. Not a Domain, not a Faculty, not a pipeline stage - see § Domains/Faculties above and "Architectural placement" below for why.

Vision represents the user's broader direction or desired future, optionally providing shared context for more than one Goal. It sits above the Goal → Plan → Action → Feedback → Replan loop, not inside it:

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
 ↺
```

Two things distinguish a real Vision from a renamed Plan - this distinction is the reason the concept was worth building at all, not just documenting:

- A single goal's own longer-horizon content ("write lyrics, book studio time" for "make a song") is scoped to *one* goal_id. That's Plan, at a broad timescale - already correctly Plan, not Vision, and unchanged by any of this.
- "Improve physical health and quality of life" informing *several independent* goals ("get visible abs," "improve cardio," "improve sleep") is scoped across goal_ids. Nothing represented this before 2026-08-26 - this is what Vision actually is.

**What's built.** A Vision is `{id, user_id, text, created_at}`, stored in its own file, `data/visions.json` - deliberately separate from `data/plans.json`, no relation between the two beyond a Goal record optionally carrying the id (see below). Created via the "Set a vision" form (`devtools/html/set_goal/_vision_form.html`, `POST /vision`); listed and selectable when creating a goal. A Goal record may carry an optional `vision_id` (see `backend/infrastructure/data_persistence.py`'s `save_plan()`/`save_vision()`/`load_visions()`/`get_vision()`) - `None` is the normal case, not a gap to fill in. Set once at goal creation, carried forward unchanged across every later replan for that goal (same treatment as `frozen_duration`: a goal's Vision doesn't change just because its Plan does). In the interface, goals sharing a `vision_id` render grouped under its heading, above the goal collection, never inside an individual goal's card (`devtools/app.py`'s `_group_active_by_vision()`) - Vision is not styled as another Plan time horizon (see `devtools/css/style.css`'s `.vision-heading`, deliberately distinct from `.model-label`).

**What's not built, on purpose.** No editing or deleting an existing Vision (create-only). No automatic goal generation from a Vision, and no Vision text supplied to the LLM yet at all - `generate_plan()`/`replan()` (`backend/planning/plan.py`) both currently ignore a goal's `vision_id` entirely; their docstrings mark the exact spot where a short Vision summary could eventually be appended to the model's context, the same way `duration` already is. The relationship, if that's ever built, stays "Vision contextualizes Goals," never "Vision generates Goals."

**Why this shape.** [[05-decisions]] already considered essentially this need once before, from a different angle - "multiple life-domains (health/work/finance) reasoning about each other" - and concluded it should be lightweight context, not a relational join. This implementation follows that precedent: a small separate id+text store plus an optional foreign-key-style reference, the same pattern `goal_id` itself already uses, not a hierarchy. Duplicating the Vision's text directly onto every goal record (instead of a shared id) was rejected for the same reason goal identity moved off free-text years ago in this project's own history: two goals with independently-typed, slightly different vision text would silently fork into two visions instead of sharing one. See [[05-decisions]] for the full comparison of alternatives.

[[00-project-brief]] § Product Philosophy's "the life domain is secondary" remains a standing caution, not a blocker: Vision stays optional context a Goal can carry, never a required organizing layer every Goal must sit under.

**Architectural placement.** Not a Domain, Faculty, or pipeline stage. Per the Faculty rule applied elsewhere in this document (see [[05-decisions]], "Faculty categorization"), nothing here has demonstrated reusable understanding across Domains - Vision's storage functions live directly in `data_persistence.py` (Infrastructure: they move/store, they don't interpret), and its only consumers today are Goals/Planning.

### Knowledge — Domain

Knowledge allows the agent to reason using material supplied by the user rather than relying exclusively on model knowledge or live external information.

The planned architecture is retrieval-based:

```text
User documents
      ↓
Retrieval
      ↓
Relevant context
      ↓
Reasoning
```

The implementation should remain local and simple until scale creates a real need for dedicated retrieval infrastructure.

A fact-checking capability built on top of this Domain - verifying a claim against retrieved sources rather than answering from training alone - is a parked idea, not yet designed: see [[06-development]] § Parking Lot.

### Memory — Domain

Memory is the agent's accumulated record of the user's goals, plans, activity and history.

It should remain local, portable and independently accessible from the application itself.

The exact long-term retrieval and organization model is intentionally not fixed yet. Whether a corresponding Faculty (e.g. how the agent selects, interprets, and relates past experience) eventually emerges is deliberately left open, not decided now.

See § Long-term architecture below for an exploratory hypothesis about a representation derived from this Domain's history, distinct from the raw record itself.

### World — Domain

World represents live external information and services the agent may eventually use when reasoning or acting — for example weather, calendars, maps and other external sources.

World is distinct from Knowledge:

* **Knowledge** = material the user has supplied
* **World** = live information from external systems

---

## 6. Long-term architecture

> Vision, not current implementation.

The long-term system can be understood as a loop between the user, the world, the agent's memory and its reasoning:

```text
                     PERSONAL AGENT

                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
       MEMORY            WORLD             USER
          │                │                │
          │          information          goals
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                       REASONING
                           ↓
                  ┌────────┴────────┐
                  ↓                 ↓
               PLANNING           ACTION
                  ↓                 ↓
               schedule       interaction
                  │                 │
                  └────────┬────────┘
                           ↓
                        RESULT
                           ↓
                         MEMORY
                           ↺
```

Future interfaces — web, iOS or Android — should sit above the same backend and portable data rather than defining the underlying architecture.

Future synchronization should preserve the local-first principle: the user's devices remain authoritative, while synchronization infrastructure acts as a replaceable mechanism rather than the owner of the data.

None of this is being built as part of the current MVP. See [[02-product]] and [[06-development]].

### Adaptive user representation and relational continuity (exploratory)

> Hypothesis under exploration as of 2026-08-26, not a design commitment. Nothing described in this subsection exists in the codebase; see [[04-current-state]] for what's actually built.

Beyond an LLM, prompts, and memory as retrieval of past conversation, the agent could in principle maintain a small, persistent representation of the user that is shaped and updated by experience, rather than only stored and looked up:

```text
experience
    ↓
memory / raw events
    ↓
adaptive internal representation
    ↓
expectation
    ↓
new observation
    ↓
discrepancy
    ↓
updated internal state
    ↓
changed future behaviour
```

This separates two things that retrieval alone does not distinguish:

- **Raw memory** — what happened: individual events, as a record. This is what § Memory above already describes, and what `foundation/memory/` is a scaffold for.
- **Adaptive representation** — what has been generalized from what happened: a compact, updated statistic (e.g. an expected rate, or a belief with a confidence) that is shaped by every observation and used to interpret the next one, instead of being re-derived from raw records each time.

The property that matters is a native notion of *expectation* and *discrepancy*. Retrieval finds records similar to a query; on its own, it does not produce "this differs from what has been observed for this person" as a first-class signal — that requires some form of persistent, incrementally updated state.

Not a requirement to use a neural network. The open question is not "how is a neural network added to the agent" but "how could the agent's internal representation of the user actually change through experience, at all." A small neural network is one possible future implementation of such a representation. Given a single-user, low-volume, non-stationary source of data (see [[04-current-state]]), a simpler mechanism — an exponential moving average, Bayesian updating, or another lightweight statistical estimator — is more likely to be the right starting point, for the same reason [[05-decisions]] already gives for keeping other true/false judgments (e.g. outcome classification) deterministic rather than model-based: interpretability, and resistance to acting on too little data, matter more here than representational capacity. A mechanism like this would sit alongside, not replace, deterministic logic and LLM reasoning — the same layering already used elsewhere: code decides what it can, a lightweight model estimates what depends on accumulated personal history, the LLM handles language.

Whatever the mechanism, the representation should remain derivable from the raw event log, not the only record of it — Memory stays the source of truth (see § Architectural principles, "Local-first" and "Portable"); an adaptive representation is a rebuildable derived state, not a replacement for it.

**Relational continuity.** A related hypothesis: continuous recognition of the user, and behavior that visibly reflects accumulated history with them specifically, may be what gives an agent relational continuity over time — not a simulated personality or emotional behavior. The distinction drawn: the aim is for the user to experience "this is the same entity I've dealt with before," not "this is a person" — recognition and consistency, not anthropomorphism. If built, this would show up as the agent's behavior visibly depending on what it has previously observed about this specific user (e.g. a plan revision or a check-in shaped by their own prior pattern, rather than a generic response) — not as a claim the agent makes about itself.

**Terminology note.** "Primal intelligence" is used here as an informal, exploratory working term for a question — roughly, what is the smallest set of mechanisms giving an agent its own goal-directed, adaptive behavior, before relying on progressively larger models and tools — not as an established technical term, a proposed Domain/Faculty name, or a claim about the system's implementation. Persistent internal state, recognition, expectation, discrepancy-detection, and adaptive behavior do not require or imply subjective experience; nothing in this subsection is a claim about machine consciousness.

**Architectural placement.** None of this is placed as a Domain or Faculty. Per the existing rule for what qualifies as a Faculty (see [[05-decisions]], "Faculty categorization"), a Faculty must be reusable understanding demonstrated across more than one Domain, not created because a concept has a plausible name. Today, an adaptive user representation would only be relevant to Planning and Goals. If built, it belongs as a capability internal to those Domains, not a new Domain or Faculty — unless a similar need for it later appears in another Domain (e.g. Knowledge or Conversation), at which point it would meet the project's own bar for becoming one.

See § Parking Lot in [[06-development]] for two smaller, related interface ideas explored alongside this: a minimal visual identity for the agent, and a "notice" interaction surface for a detected discrepancy.

---

## See also

* [[02-product]]
* [[04-current-state]]
* [[05-decisions]]
* [[06-development]]
