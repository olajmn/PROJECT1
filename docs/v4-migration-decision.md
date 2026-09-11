# V4 Migration — Decision Record

> The target architecture the project is now migrating toward: a human-facing interface, a conversation parser, a capability selector, one or more capabilities (Planning first), and a deterministic program underneath them. This document is the pre-implementation map for that direction — it describes responsibility, boundary, relationship, and data flow, not classes, file paths, or schemas. Written before any code for this architecture exists, so that implementation follows an explicit boundary instead of one discovered by accident while writing code.

## Contents

- Status
- Architectural intent
- Current system (today)
- Target architecture — system overview
- Core roles
  - LLM1 — Human Interface
  - LLM2 — Parser / Compiler
  - LLM3 — Capability Selection
- Capabilities
  - Planning
- Deterministic Program
- Data flow
- Context and scope: scoped vs. free conversation
- UI manifestation
- Faculties
- The agent, precisely
- Boundaries and non-responsibilities
- Current → Target
- Open questions
- Related documentation

## Status

**Decision.** The direction described in this document — LLM1 / LLM2 / LLM3 / Capability / Deterministic Program — is settled, not under discussion. What is *not* settled is the exact shape of several boundaries between these roles; those are marked as open questions below and are expected to be resolved through prototyping, not through further up-front design.

This document is documentation-only. No code, route, template, or existing Planning logic changes as a result of writing it.

It complements, rather than replaces, existing documentation:

- `03-architecture.md` describes the current Domains/Faculties/Pipeline model and its own, more speculative, Long-Term Architecture section (§6) — this document is the concrete near-term target that section's spirit points toward, for the interface/reasoning layer specifically.
- `planning-model.md` remains the authority on what Planning's own domain concepts (Goal, Minimum Planability, ASK/SUGGEST/PLAN, Progression, Action, Feedback, Replanning) mean. This document does not redefine any of them — it only says where Planning as a whole sits relative to LLM1/LLM2/LLM3.
- `04-current-state.md` remains the authority on what is actually built right now.

## Architectural intent

The prototype today has exactly one LLM-shaped boundary, and it does three unrelated jobs inside one model call: deciding whether a goal is understood well enough to act on (Minimum Planability), producing the actual plan content, and — implicitly — being the only thing anywhere in the system that decides "what happens next," a decision actually made today by which HTML page and button the user happened to use, not by any reasoning step.

The intent behind this migration is to separate three questions that are currently fused:

1. *How do I talk to this person right now?* (LLM1)
2. *What are they actually asking for, in a form the rest of the system can use, regardless of which capability ends up handling it?* (LLM2)
3. *Given that, does anything need to happen, and if so, which capability handles it?* (LLM3)

...from the fourth question, which the prototype already answers reasonably well and which this migration does not want to disturb:

4. *Given that Planning is the relevant capability, how does Planning itself reason about and act on this?* (the Planning capability's own business, unchanged in kind)

A further intent, made concrete by the recent model swap (`05-decisions.md` #21), is that a *role* (LLM1, LLM2, LLM3, or a capability's own internal reasoning) and the *model* behind it are different things. The existing `backend/reasoning/model_client.py` pattern — one small module, one named model constant, one function, no caller aware of which model answers — already proves this works, and is the pattern this architecture expects to repeat per role rather than invent something new for.

## Current system (today)

Full detail: `04-current-state.md`. Summarized here only as much as the mapping in this document needs.

- **One LLM boundary.** `backend/reasoning/model_client.py:send_message()` is the only place `ollama.chat()` is called. Three independent callers use it, all inside what is today informally "the planning stack": `backend/goals/plan/model_client.py:ask_model()`, `backend/goals/plan/step_generator.py:generate_steps()`, and `backend/goals/feedback/acknowledger.py:acknowledge()`.
- **No LLM1, LLM2, or LLM3 exist in any form today.** The `/` Conversation page is a disabled placeholder. What happens next is decided entirely by which of the six work-area routes (`frontend/app.py`) the user is on and which button they pressed — capability selection is a navigation choice, not a reasoning step.
- **One model call does the work of Minimum Planability, ASK/SUGGEST, and plan-content generation together.** `backend/goals/plan/planner.py`'s `generate_plan()`/`replan()`, via `ask_model()`, decide in one round-trip whether a goal is too vague (ASK), whether a default duration or a generic first action can be proposed (SUGGEST), and produce the actual horizon content (PLAN).
- **Deterministic logic already exists and is already cleanly separated from LLM calls:** `backend/goals/feedback/feedback_parser.py` (free text → outcome, no LLM), `backend/foundation/time/` and `backend/foundation/math.py` (the two established Faculties), `backend/infrastructure/data_persistence.py` and `backend/goals/goal/resolver.py` (state/persistence), and the orchestration logic in `planner.py` itself (`create_goal`, `apply_feedback`, `advance_step`, `set_goal_vision`, `archive_vision`, `cancel_goal`).
- **`backend/memory/` and `backend/world/` are empty placeholders** — no behavior to migrate.
- **The UI (`frontend/`) already does not make domain decisions** — `frontend/view_data/` shapes already-decided data for templates; it does not decide anything about a Goal, Plan, or Vision (see `04-current-state.md` §4).

## Target architecture — system overview

```text
                         USER
                           ↕
                    ┌─────────────┐
                    │    LLM 1    │
                    │  INTERFACE  │
                    └──────┬──────┘
                           ↕
                    ┌─────────────┐
                    │    LLM 2    │
                    │    PARSER   │
                    └──────┬──────┘
                           │
                    conversation-level
                    understanding
                           │
                     ACTION NEEDED
                           ▼
                    ┌─────────────┐
                    │    LLM 3    │
                    │    AGENT /  │
                    │  CAPABILITY │
                    │  SELECTION  │
                    └──────┬──────┘
                           │
                     CAPABILITY
                       (Planning first)
                           │
                           ▼
                  DETERMINISTIC PROGRAM
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                   UI          WORLD
                    │
                    ▼
                  USER
```

Not every turn of conversation traverses the whole diagram — see "Context and scope" below.

## Core roles

### LLM1 — Human Interface

**Responsibility:** the natural conversation with the person, and presenting the conversation's own responses. LLM1 is the only role that talks to the user directly.

**Needs to know:** the ongoing conversation history/context; a light-weight sense of what currently exists (e.g. that the user has some active Goals or Visions, by name) so it can refer to them naturally.

**Must not need to know:** anything about how any capability works internally. LLM1 has no business knowing what `PLAN_KEYS`, `step_status`, `suggested_action`, or `current_step` are.

**Must not be:** Planning. LLM1 does not decide whether a goal is plannable, does not produce plan content, and does not run Minimum Planability's judgment.

### LLM2 — Parser / Compiler

**Responsibility:** transform the human conversation into a structured, capability-agnostic understanding — "what is this person actually talking about," not "what should Planning do about it."

**Produces:** something a capability-selection step can act on without having already done the capability's own reasoning — roughly, the relevant content of what was said, and which existing entity (if any) it seems to concern.

**Must not produce:** capability-specific concepts. In particular, LLM2's output must never itself be `suggested_action`, `current_step`, `step_status`, or `plan.now` — those are Planning's own vocabulary, produced only once Planning is actually reasoning about the situation. If LLM2's output starts to look like a half-finished Plan, it has taken on Planning's job.

### LLM3 — Capability Selection

**Responsibility:** decide *whether* a capability needs to run at all, and if so, *which one*. Nothing more.

**The distinction this document insists on:**

```text
LLM3 asks:      "What capability does this situation need?"
Capability asks: "How does Planning (or whichever capability was
                   selected) actually handle this situation?"
```

**Must not:** absorb any part of a capability's own domain logic. LLM3 does not evaluate Minimum Planability, does not decide ASK vs. SUGGEST vs. PLAN, and does not touch a capability's state. Its output is a routing decision plus whatever LLM2 already produced — not a re-interpretation of it.

## Capabilities

### Planning

Planning is the first capability, and it is not merely "generate a plan." It is the entire existing responsibility already developed and partly built in this project:

```text
Goal
Minimum Planability
ASK / SUGGEST / PLAN
Current / Desired State
Progression
Plan
Action
Feedback
Replanning
deterministic Planning state (persistence, Time/Math use, feedback parsing)
```

None of this moves to LLM2 or LLM3 because of where it happens to sit in the data flow relative to them. Planning is reached *through* LLM3's routing decision, but everything that happens once Planning is selected — including Planning's own use of an LLM for the parts that genuinely require language reasoning (deciding whether a goal is vague, producing plan content, generating step text) — remains entirely internal to Planning. This mirrors what is already built: `backend/goals/plan/planner.py`'s own use of `ask_model()`/`generate_steps()` alongside deterministic logic (Time/Math Faculties, `feedback_parser.py`, persistence) does not change in kind — only in what sits in front of it (a route today, LLM3's dispatch under the target architecture, or a direct call in a scoped context — see "Context and scope").

A capability is therefore not "an LLM call." It is a bounded domain responsibility that uses both LLM reasoning and deterministic program logic internally, in whatever mix its own domain actually requires — exactly the "code decides, the model is told" split already established for Time and Math (`03-architecture.md` §5), generalized to a whole domain rather than one Faculty.

Future capabilities (Shopping, Research, Coding, ...) are a scalability property of this shape, not something built now (see "Prototype, not framework" in the parent conversation's own scope instruction — not repeated as a rule here, only acknowledged).

## Deterministic Program

The deterministic program is the part of the system that does not reason in natural language and is not expected to. Its role, stated as a principle rather than an exhaustive list:

> LLMs reason and interpret; deterministic software handles what requires determinism, state, persistence, validation, and concrete execution.

Concretely, today, this already includes:

- state and persistence (`backend/infrastructure/data_persistence.py`, `backend/goals/goal/resolver.py`)
- validation of LLM output shape (`backend/goals/plan/model_client.py:ask_model()`'s required-key check)
- deterministic calculations and interpretation where the input is unambiguous (`backend/foundation/time/`, `backend/foundation/math.py`)
- feedback parsing where the judgment is deliberately kept out of LLM hands (`backend/goals/feedback/feedback_parser.py`) — this is a considered decision, not an oversight (see `05-decisions.md` #1), and stays deterministic under this architecture for the same reason
- UI manifestation (see below) and, eventually, any World/Reality connection (`backend/world/`, still empty)

This is not offered as a complete taxonomy. Where a capability's own state/persistence needs diverge from Planning's (a future capability might need different state shapes), that is left to be discovered when such a capability is actually built, not designed for now.

## Data flow

Minimum shape, described conceptually — no schema is implied by the arrows below:

```text
LLM1 → LLM2
  natural language + relevant conversational context

LLM2 → LLM3
  structured, capability-agnostic understanding of what the
  conversation currently concerns

LLM3 → Capability
  capability selection + the relevant understanding from LLM2
  (LLM3 does not re-derive or restate it)

Capability → Deterministic Program
  structured result, state change, or a requested concrete action

Deterministic Program → UI / World
  manifestation of the result; where relevant, an effect on the
  world outside the conversation

UI / World → USER
  the visible/interactive outcome
```

**One boundary is deliberately left open, not specified here:** how a capability's own conversational output (a clarifying question, a proposed default awaiting confirmation — i.e. Planning's existing ASK/SUGGEST content) travels back to the user. The diagram's forward arrows go through Deterministic Program → UI, which fits a *structural* result (a plan, a status change) but does not obviously fit genuinely conversational content that still needs LLM1's voice. This is listed under Open Questions rather than resolved here, because resolving it well likely needs to be informed by actually building the free-conversation entry point (see "Context and scope").

## Context and scope: scoped vs. free conversation

LLM3 does not need to run on every message. Its job — deciding which capability applies — has nothing left to decide once a conversation is already known to concern a specific capability and a specific entity within it (for example: an existing Goal's own ongoing thread, where the capability is already Planning and the entity is already that Goal).

The architecture therefore supports two shapes of the same flow:

```text
Free conversation:
  USER → LLM1 → LLM2 → LLM3 → Capability

Known capability context:
  USER → LLM1 → (known Capability, LLM3 not re-run)
```

Which of today's existing interaction surfaces falls into which shape is explicitly not decided in this document — see Open Questions. The principle is only that a capability, once already established for a given context, is not re-selected on every subsequent turn inside that same context.

## UI manifestation

The interface is where the system's understanding and results become visible and interactive — it is not where reasoning happens, and it does not need to know why a result looks the way it does, only how to render it and how to relay an interaction back.

```text
Conversation
    ↓
structured result (produced by a capability, shaped by the
    deterministic program)
    ↓
manifestation
    ↓
interactive UI
```

Illustrative only, not a commitment to this exact example being built: a request to plan drinking a glass of water in three steps could resolve to a structured three-item result, which the UI manifests as `●──●──●` with per-point interaction — the LLM never produces UI markup, and the UI never decides what the three steps are.

This document does not specify what "structured result" looks like, how many kinds of manifestable unit exist, or how the existing `frontend/view_data/` modules relate to it going forward — that is implementation-phase work, informed by (but not required to duplicate) the minimal-representation reasoning already explored earlier in this project's own analysis (a small, generic, addressable unit was sufficient there; whether that finding survives contact with a second capability is still open).

## Faculties

Time and Math remain exactly what they are today (`03-architecture.md` §5) and are not refactored by this document. The only architectural note worth recording here, as a tentative idea rather than a committed design:

> A Faculty is a shared domain capability/understanding that may be used across multiple LLM roles and/or deterministic program logic, not owned by any single capability.

This is an extension of the existing Faculty concept (previously scoped to being used *within* the agent's own reasoning) to also being potentially reusable *by* LLM1/LLM2/LLM3 directly, not only by a capability. It is recorded because it is a plausible consequence of introducing multiple LLM roles, not because a Faculty framework is being built now. No new Faculty is proposed, and the existing Faculty bar (`05-decisions.md` "Faculty categorization" and its refinement) is unchanged.

## The agent, precisely

"Agent" is used carefully here, on purpose. It does not name a new, separate component. Under this architecture:

```text
Agent = LLM3 + capabilities + deterministic program + state + interface
```

LLM3 is the component that selects and directs a capability; it is not, by itself, "the agent." There is no additional layer named something like "Agent Intelligence" sitting above or beside LLM3 with its own undefined responsibility — if such a thing turns out to be needed, it must be justified the same way a Faculty is (demonstrated need, not a plausible name), and is explicitly not introduced by this document.

## Boundaries and non-responsibilities

Stated explicitly, to make later drift visible rather than silent:

- LLM1 does not decide, plan, or select capabilities.
- LLM2 does not decide capability selection, and does not produce capability-specific fields.
- LLM3 does not perform a capability's own domain reasoning, and does not touch a capability's state directly.
- Planning does not get absorbed into LLM2 or LLM3 merely because it is conceptually "in the flow" between them.
- The deterministic program does not reason about ambiguous input in natural language; where a judgment about ambiguous text is required (e.g. "did the user say they completed this"), it stays inside a capability's own deterministic logic (`feedback_parser.py` today), never becomes an LLM2-level generic judgment.
- The UI does not decide anything about a Goal, Plan, or Vision, and does not host any reasoning — unchanged from the current, already-enforced rule (`04-current-state.md` §4).

## Current → Target

| | Current | Target |
|---|---|---|
| LLM boundary | One (`backend/reasoning/model_client.py`), shared by all three existing model calls, all inside "planning" | One boundary pattern, repeated per role (LLM1, LLM2, LLM3), each independently swappable — plus Planning's own existing internal use of the same underlying pattern |
| Capability selection | None — a navigation choice between six hardcoded routes | LLM3, run only where the capability/context is not already established |
| Minimum Planability / ASK / SUGGEST / PLAN | Inside one combined model call in `generate_plan()`/`replan()` | Unchanged in kind — stays entirely inside the Planning capability's own internal reasoning |
| Plan content generation | Same combined call, plus `step_generator.py` as a second, narrower call | Unchanged — both remain Planning-internal LLM usage |
| Deterministic outcome parsing | `feedback_parser.py`, no LLM | Unchanged, stays deterministic, stays Planning-internal |
| Time / Math Faculties | Deterministic, used by Planning | Unchanged; the "shared across LLM roles too" extension is a tentative note, not a rebuild |
| State / persistence | `data_persistence.py`, `goal/resolver.py` | Unchanged |
| `acknowledger.py` (warm, non-deciding conversational acknowledgment) | Called from inside Planning's `apply_feedback()` | Flagged as conceptually belonging closer to LLM1 (it produces conversational text, not a domain decision) — not moved by this document; see Open Questions |
| Six work-area routes (goal-vision, goal-cancel, step, history, completed, active) | Direct, unconditional calls to deterministic Planning functions | Expected to remain direct calls with no LLM in front of them — they are already unambiguously scoped and require no capability selection |
| `/set-goal` (free-text new goal) and `/` (Conversation, today inert) | `/set-goal` calls Planning directly; `/` does nothing | The natural home for LLM1 → LLM2 → LLM3 → Planning, built additively alongside the existing routes, not replacing them yet |
| UI (`frontend/view_data/`, templates) | Already makes no domain decisions | Unchanged for now; a more generic manifestation layer is a later question, only if/when a second capability makes the current, Planning-specific shape genuinely insufficient |
| `backend/memory/`, `backend/world/` | Empty | Unchanged; confirmed, not contradicted, as the eventual home of World/Reality |

## Open questions

Deliberately left open — expected to be resolved by building and observing, not by further design:

- The exact return path for a capability's own conversational output (an ASK question, a SUGGEST awaiting confirmation) back to the user: through LLM1, or shown directly as today's per-Goal thread already does.
- How much conversational context LLM2 actually needs to produce a useful, capability-agnostic understanding — untested.
- Precisely when LLM3 should be bypassed (which existing surfaces count as "already scoped") — named as a principle here, not yet mapped onto specific routes.
- The exact boundary between LLM1's own conversational language and a capability's generated language, once both can appear in the same thread.
- How UI manifestation should represent a capability's result in general — the minimal-representation reasoning already explored elsewhere in this project's analysis is a candidate starting point, not adopted here.
- The Faculty-across-roles idea above — recorded, not designed.
- Whether `acknowledger.py`'s responsibility actually moves to LLM1, and if so, when — noted as a likely candidate, not scheduled.
- Which of today's six work-area routes, if any, eventually route through LLM1/LLM2/LLM3 versus permanently staying direct, deterministic entry points.

## Related documentation

- `03-architecture.md` — current Domains/Faculties/Pipeline model; §6 for the more speculative long-term direction this document narrows and makes concrete for the interface/reasoning layer.
- `04-current-state.md` — what is actually built right now; authoritative for verifying any claim in this document's "Current system" section against the live code.
- `planning-model.md` — the conceptual meaning of Goal, Minimum Planability, ASK/SUGGEST/PLAN, Progression, Action, Feedback, Replanning, unchanged and un-redefined by this document.
- `05-decisions.md` — decision log; entry #21 (the model-swap decision) is the concrete precedent this document's role/model distinction builds on. No entry yet records the architecture direction itself — see the closing report for this analysis for whether one should be added.
