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
| Minimum Planability | Partially established | Content-vagueness (ASK), content-level SUGGEST (`suggested_action`), and time-sufficiency (`suggested_duration`) are all explicit now; the state/capacity dimension of the gate is still undeveloped, and how several simultaneous unknowns compose is still only described by example (see `docs/planning-model.md` § Minimum planability, Open questions). |
| Conversation (per-Goal thread) | Partially established | Mechanically works, and now has an explicit SUGGEST-and-confirm path for the specific "user doesn't know what to do" case (see `docs/planning-model.md` § Interpreting a response to ASK/SUGGEST) — but live testing (2026-09-08) found the model's use of that mechanism unstable across otherwise-identical runs (see "Known functional gaps" below). |
| SUGGEST → confirmation → Action | Partially established | Wiring verified deterministically (accept / explicit alternative / Current-State correction all route correctly; `current_step`/`step_status`/Vision/history preserved). Live model behavior on the reply-interpretation step is unstable — see "Known functional gaps." |
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
- **Content-SUGGEST confirmation (2026-09-08)** - `generate_plan()`
  gained an explicit `suggested_action` mode (content-level SUGGEST,
  parallel to `suggested_duration`); `apply_feedback()` gained a
  matching branch that treats acceptance as the proposal becoming
  `plan.now` directly (no `replan()`, no Action marked completed), and
  treats anything else as new information re-evaluated through
  `generate_plan()` again. Verified deterministically
  (`backend/goals/plan/test_planner.py`, 9 scenarios: accept / explicit
  alternative / Current-State correction / full accept→Done chain /
  ordinary Action's "Yes" unaffected / existing `suggested_duration`
  and `clarification` flows unaffected / state preservation across
  confirmation).
- **ASK/SUGGEST as interaction, not just decision (2026-09-08)** -
  `docs/planning-model.md` now documents that a user's reply to a
  pending ASK/SUGGEST must be interpreted relative to the agent's own
  prior contribution (`X`), not read as free-standing Goal text; three
  semantic relations named (Observation/Evidence, Directly supplied
  KNOWN, No new information); kept as a distinct, pre-commitment
  sibling to the existing post-execution Feedback/Replanning loop, not
  merged with it. See `docs/planning-model.md` § Interpreting a
  response to ASK/SUGGEST.

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
- **The SUGGEST/ASK flow, now mechanically built for the "user doesn't
  know what should be done" case, does not yet produce stable model
  behavior** - `suggested_action` + confirmation is wired and verified
  deterministically (see "Completed / stabilized"), and a follow-up
  experiment (2026-09-08) confirmed the model does receive its own
  prior suggestion and the user's reply as explicit, correctly-labeled
  context (verified by capturing the exact prompt text, not assumed) -
  but live behavior swung from using that context in roughly 10/11
  calls in one batch to roughly 1/11 in an otherwise-identical batch.
  Now understood as a model-stability question, not a missing-context
  or missing-mechanism question - see "Next reasoning experiment"
  below.
- **Multi-round information doesn't reliably accumulate into a
  visibly updated understanding** - the Learning goal case
  (2026-09-08: user progressively said "not sure" → "want to become
  more physically active" → "something that makes my body more
  active" → "condition") kept receiving very similar re-phrased
  questions despite each reply adding real information. Distinct from
  the `clarification`+`now` leak below - this is about whether
  accumulated replies actually change what the agent asks or suggests
  next, not about what gets displayed.
- **A pre-existing `clarification`+`now` leak, confirmed empirically
  (2026-09-08)** - when the model sets `clarification` it does not
  reliably leave `now` null despite being told to (observed live in
  the Learning goal case: a stray, unrelated Action shown alongside an
  ASK question). `generate_plan()` defensively nulls `now` when the
  newer `suggested_action` is set, but the older `clarification`
  branch was deliberately left as-is when that defensive check was
  added - a known, narrow, still-unfixed gap, not a new one.
- **SUGGEST can smuggle in an unstated personal assumption** - the
  move-city case ("research cities and their job markets") privileged
  career as the reason for moving, when family/cost/climate/lifestyle
  are equally plausible. `docs/planning-model.md` § ASK vs. SUGGEST now
  names a test for this (would the suggestion remain reasonable across
  plausible alternative motivations) - nothing enforces it yet.
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
- Whether the agent's need to track its own prior ASK/SUGGEST
  contribution generalizes into something like a self-model / agent
  continuity - flagged as an open architectural hypothesis, not
  decided or built (see `docs/03-architecture.md` § Long-Term
  Architecture, "the self-model," and `docs/planning-model.md` § Open
  questions).

## Suggested next milestone

**Hypothesis, not a decision.** The narrow diagnosis this section
previously called for is now done (2026-09-08, across several passes:
a forensic trace of the actual `apply_feedback()`/`generate_plan()`
code path, a conceptual precision of what ASK/SUGGEST-as-interaction
actually means - now `docs/planning-model.md` § Interpreting a
response to ASK/SUGGEST - and a live experiment). The finding: this is
not a missing-context problem (verified: the model does receive its
own prior contribution and the user's reply, explicitly labeled) and
not a missing-mechanism problem (the `suggested_action` + confirmation
path is built and deterministically tested) - it is model-behavior
instability: an otherwise-identical prompt produced very different
reply-interpretation rates (~10/11 vs. ~1/11) across two live batches.

**Next reasoning experiment (not yet run).** The experiment already
run included a basic instruction telling the model to read the reply
in light of what it just suggested - that alone did not stabilize the
behavior. The next pass should test whether a *sharper* or
differently-framed version of that instruction (not merely the
presence of one, which is already partially tested) measurably reduces
the variance observed:

```text
Previous contribution X
+
User response Y
+
a sharper, more explicit instruction to interpret Y relative to X
→ more stable updated understanding?
```

Still an experiment, not a decided fix - if a sharper instruction
doesn't stabilize it either, that would be further evidence toward a
genuine `llama3.1:8b` limitation rather than a prompt-framing gap.

## Other, parked

- **Revisit visual design holistically, not one color at a time** -
  disliking the purple `.model-label`/`.yaml-key` color (`#7c3aed` in
  style.css) was the trigger, but the actual ask is a holistic pass
  over the interface's visual language, not a single-color fix. Raised
  2026-08-23, untouched since.
