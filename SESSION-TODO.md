# Session TODO

The working scope and maturity map for the **active development
phase** - right now, that phase is the Active Goal loop (`Vision →
Goal → Plan → Step → Action → Reality → Feedback → Replan`). Not part
of the docs/ vault (that's permanent project documentation), and not a
general backlog of everything the project could ever build - Memory,
Knowledge/RAG, and Acting stay named here only as things *outside* the
current phase, not sequenced within it.

Three documents, three different jobs - don't collapse them:

- **`docs/planning-model.md`** - what the planning concepts (Goal,
  Plan, Step, Action, Reality, Verification, ...) actually *mean*.
- **`docs/04-current-state.md`** - what the system actually *is and
  does* right now.
- **This file** - what remains within the active phase's scope, how
  mature each part of it is, which functional gaps and conceptual
  questions are still open, and what's deliberately parked. It defines
  and tracks the scope and its remaining maturity; it does not replace
  either of the other two.

A line item here is not automatically an implementation task - some
need their own `question → analysis → discussion → decision →
implementation → verification` pass before they're ready to code
(exactly how today's Step/Action Design A got built). Staying within
the Active Goal loop as the active phase means working through what's
below before jumping to a different major area (Memory, RAG, Acting),
not that every remaining item here is queued up next.

Rewritten 2026-09-07 after a session of conceptual analysis (see
`docs/planning-model.md`) and the resulting Step/Action Design A
implementation; earlier content is folded into the sections below
rather than kept as a separate log.

## Active Goal loop - maturity map

A snapshot of how mature each part of the `Vision → Goal → Plan → Step
→ Action → Reality → Feedback → Replan` loop actually is, right now -
not a roadmap, not a ranked feature list. "Not yet built" does not
mean "next" - it only means the concept is named but has no
implementation behind it yet. Added 2026-09-07; re-derive rather than
trust this indefinitely once real work changes any of it.

- **Established** - built, verified, and stable within its own
  deliberately limited scope.
- **Partially established** - a real, working first version exists,
  but it doesn't yet cover the whole concept as currently understood.
- **Not yet built** - the concept is named and understood; no
  implementation exists.

| Component | Status | Note |
|---|---|---|
| Goal | Established | Identity/history via `goal_id`, unchanged for a long time. |
| Vision | Established | Create/list/archive, link/detach, now supplied as context to planning calls - within its own accepted scope (no editing, no summarization). |
| Multi-goal display | Established | Active goals grouped/shown together (`goal_overview.py`) - distinct from multi-goal *reasoning*, below. |
| Plan generation | Established | The ASK/SUGGEST/PLAN-gated model call producing horizon text + a step list. |
| Action formulation | Established | The mechanism that produces concrete next-step text (`plan.now`/`steps[i]`) - separate from whether Conversation exposes it well (see below). |
| Basic feedback ingestion | Established | Deterministic outcome/duration-change parsing (`feedback_parser.py`), well-tested. |
| Replanning mechanism | Established | The model call runs and saves reliably - this is the machinery only, not conceptual completeness (see "Feedback → updated understanding → Replanning" below). |
| Step model | Partially established | Flat generation works for short/medium goals; known to produce too-coarse steps for long-duration ones (see "Vertical/hierarchical step list" below). |
| Step resolution / Verification (self-report only) | Partially established | Design A (`open`/`resolved`) is real and verified, but script-tested only so far, not yet exercised through live browser use, and doesn't cover compound conditions (the PC-building case) or habit-shaped steps. |
| Minimum Planability | Partially established | Content-vagueness and time-sufficiency covered; the state/capacity dimension of the gate is undeveloped. |
| Conversation (per-Goal thread) | Partially established | Mechanically works; empirically fails the ASK→SUGGEST transition when the user says they don't know what to do (see `docs/planning-model.md` § Conversation). |
| Plan adaptation | Partially established | The temporal axis adapts via `replan()`; the structural axis (steps) never does. |
| Action in the execution loop | Partially established | Formulation and a real completion signal exist; situational zoom and agent-side execution don't. |
| Feedback → updated understanding → Replanning | Partially established | Genuinely updates the temporal axis; never reaches the structural axis. |
| Conversation entry point (`/`) | Not yet built | Still a disabled placeholder textarea - no intent routing at all. |
| Autonomous Action execution | Not yet built | No tool-calling/agent-operation infrastructure anywhere in `backend/`. |
| Reality/Verification beyond self-report | Not yet built | No evidence storage, confidence, or tool/system observation channel. |
| Continuity / Proactivity | Not yet built | No scheduler or background behavior anywhere - the loop only runs on an HTTP request. |
| Multi-goal reasoning | Not yet built | Goals are shown together, but nothing reasons across them (e.g. competing for time). |
| Decomposition / zoom | Not yet built | No mechanism to increase resolution on one Step on demand. |

**On merging "Vertical/hierarchical step list" into Decomposition/zoom
(considered, not done):** related, not identical. Decomposition/zoom is
a general, on-demand, per-Step mechanism; the vertical-step-list case
is a specific, already-diagnosed symptom of today's `step_count()`
heuristic producing too-coarse steps for long goals, fixable in
principle either as an instance of the general mechanism or with a
narrower tuning change alone. Kept as two separate, cross-referenced
entries below rather than merged, so neither the concrete trigger nor
the narrower fix option gets lost.

## Completed / stabilized

- **Workspace/frontend structural cleanup** - the six work-area split
  (Conversation, Set Goal, Vision, Active, Completed, History), the
  Task→Action/Vision/PLAN_KEYS terminology consolidation, and the
  `view_data/` split (`goal_overview.py`/`text_formatting.py`/
  `plan_horizons.py`) - see `docs/04-current-state.md` and
  `docs/06-development.md` for when each landed.
- **Planning model documentation baseline** - `docs/planning-model.md`
  v1 (Minimum Planability, Progression, Plan's two axes), now extended
  today with Action, Decomposition/zoom, Reality/Observation/
  Verification, Completion, and Conversation's observed limitation.
- **Minimum planability v1** - the ASK/SUGGEST/PLAN gate
  (`_planability()`, `backend/goals/plan/planner.py`) - a goal too
  vague in content gets a clarifying question; a goal with no given
  timeframe but a reasonable default gets a proposed one instead of a
  blank question.
- **Vision context** - create/list/archive, link/detach from a Goal,
  and (as of `58a8d34`, "Wire Vision context into planning and
  replanning") actually supplied as background context to
  `generate_plan()`/`replan()`'s model calls, not just stored.
  `docs/03-architecture.md` § Vision's stale "the model calls ignore
  `vision_id` entirely" claim was corrected in the 2026-09-07
  consolidation pass, along with `docs/04-current-state.md`'s matching
  stale claim.
- **Step/Action Design A** - `step_status` (`open`/`resolved`) per
  step, separate from `current_step`; an Action reported done never by
  itself resolves its Step; `current_step` only advances on an
  explicit, structured "resolved" signal. See `docs/planning-model.md`
  § Completion and § Structural axis.
- **State-integrity bugfix** - `apply_feedback()`'s `goal_completed`
  and `action_in_progress` branches were silently resetting
  `current_step`/`step_status` to their defaults on an ordinary
  check-in message (found and fixed same day as Design A).
- **Verification run** - 8 scenario tests for Design A (action done/
  not resolved, action done/resolved, action not done, repeated
  actions against one step, a legacy goal with no `step_status`,
  append-only history, replan, cancel/Vision) plus 2 targeted
  regression tests for the bugfix above, all against isolated temp
  data, all passing; every existing `test_*.py` module (`test_math`,
  `test_time`, `test_feedback_parser`, `test_data_persistence`) still
  passes; `tools/project_check.py`/`docs_check.py`/`docs_lint.py`
  clean; `/active`, `/vision`, `/history` all confirmed serving `200`.
- **Documentation/code reconciliation pass (2026-09-07)** - corrected
  the stale "Vision is ignored by the model" claim in both
  `docs/03-architecture.md` and `docs/04-current-state.md`;
  `docs/04-current-state.md` brought back in sync with actual code
  (Step/Action Design A, `action_reader.py`'s CLI-only status, the
  Vision-context fact, a new Current Decisions line for structured
  Step-resolution); removed one confirmed-dead CSS rule (`.vision-list`
  in `frontend/css/style.css`, unreferenced by any template).

## Known functional gaps

- **Conversation does not yet work as the agentic dialogue the
  conceptual model assumes** - empirically observed 2026-09-07 (see
  `docs/planning-model.md` § Conversation): told the user doesn't know
  what steps to take and wants help, the agent re-asked essentially
  the same question instead of making the ASK→SUGGEST transition
  Minimum Planability's gate describes.
- **Internal planning/reasoning leaks into, or fails to reach, the
  user-facing interaction** - the same observation showed a concrete
  Action being generated ("Make a list of your current job search
  resources...") without that reasoning surfacing constructively in
  the conversation itself. Root cause not diagnosed - see the
  Conversation entry in `docs/planning-model.md`.
- **The SUGGEST/ASK flow does not yet work robustly when the user
  themselves doesn't know what should be done** - a specific instance
  of the above, worth naming separately since it's the exact case
  Minimum Planability's "propose a default" move exists for.
- **Feedback is limited to human self-report** - there is no other
  Observation/Evidence channel yet (see `docs/planning-model.md` §
  Reality, Observation, and Verification) - deliberate for now, not a
  bug, but a real ceiling on how completion/verification can work.
- **No continuity or proactivity** - the agent never initiates
  anything; every step of the loop only runs in response to an HTTP
  request the user makes. No scheduler, reminder, or background
  behavior exists anywhere in `backend/`.
- **No multi-goal awareness** - each Goal's loop runs independently;
  Vision provides shared *text* context to planning calls, but nothing
  reasons across multiple active Goals as a set (e.g. noticing they
  compete for the same time/energy).

## Conceptual work still open

(See `docs/planning-model.md` § Open questions for the fuller,
cross-referenced list - this is a shorter pointer, not a duplicate.)

- Whether `Stage`/`Milestone` still deserve their own names, or
  "Step at a given resolution" is enough.
- Decomposition/zoom's persisted data shape (container, tree,
  replacement, or read-alongside) - deliberately left open.
- **Vertical/hierarchical step list** (raised 2026-08-23, still open,
  distinct from the above): today's flat step list is tuned for
  single-session goals: a multi-month goal produces steps that are
  really coarse phases (e.g. one step spanning 16 days), not the
  granular actions they're meant to be. Closely related to
  Decomposition/zoom but a more concrete, previously-diagnosed trigger
  case worth keeping visible on its own.
- Habit/process Step completion - what counts as sufficient evidence
  for a pattern sustained over time, not decided.
- Capacity and hard external constraints as their own instances of
  Minimum Planability's gate, vs. staying implicit.
- Whether Verification should ever become an explicit, separately-
  named phase in the control flow.
- Whether a Plan's "current understanding" should ever become its own
  small persisted field, the way `frozen_duration`/`current_step`/
  `step_status`/`vision_id` already are.
- Should a goal auto-complete once every step is resolved? Still
  deliberately not automatic (see `docs/06-development.md`,
  2026-08-23) - real tension between one-shot and habit goals, not
  reopened by today's Design A work.
- Memory, Knowledge/RAG, and Acting (the agent performing external
  actions) remain entirely unstarted - not touched by today's session.

## Suggested next milestone

**Hypothesis, not a decision.** Conversation/agentic interaction is a
reasonable candidate for the next major milestone - it's the intended
single entry point to the whole `Understand → Minimum Planability →
Plan → Action → Feedback → Replan` loop, and today's empirical test
found a concrete, reproducible failure exactly there.

Caution before committing to it as a large new line of work, though:
Conversation wasn't among the five options this project's own last
"pick ONE of these five" review named (Memory / Better step hierarchy
/ Knowledge-RAG / Acting), and the observed failure hasn't been
diagnosed yet - it could be a narrow content/prompt issue in the
existing ASK/SUGGEST model call, not evidence that Conversation needs
to become its own domain (`architecture_foundation/ROADMAP.md` already
lists "Conversation as its own domain" under "Later," not "Next," for
a different reason). The more disciplined next step is probably a
**narrow diagnosis** of why the ASK→SUGGEST transition failed in the
observed case, before deciding whether that calls for Conversation
work at all, or a smaller, contained fix elsewhere.

## Other, parked

- **Revisit visual design holistically, not one color at a time** -
  disliking the purple `.model-label`/`.yaml-key` color (`#7c3aed` in
  style.css) was the trigger, but the actual ask is a holistic pass
  over the interface's visual language, not a single-color fix. Raised
  2026-08-23, untouched since.
