# TODO

Not a duplicate of `docs/04-current-state.md` - that file is the full,
factual account of what's true now, including known bugs/gaps and the
reasoning behind each. This file only tracks which of those are
actually being worked on (**Active**), a numbered catalog of
everything identified so far, tiered by rough impact (**Queue**), and
a **Parallel paths** table of dual/redundant code to keep visible
while iterating — so both the total scope and what must not silently
accumulate are visible at a glance.

An item moves from Queue to Active only when deliberately chosen as
next; it stays in Queue, undecided, until then - a known gap does not
need to be urgent to be worth recording (see `docs/04-current-state.md`
for that same principle applied to documentation, not just this file).

## Active

**23. Goal → Project migration** (~~Phase A + B compat done~~ 2026-09-20)

Product [[05-decisions]] #25; wire [[05-decisions]] #29 /
[[goal-to-project-migration]]. Primary: `project_id`, `/api/projects`,
llm3 `"project"`. Engine: `judgment/` + `when/` (plan folder gone).
Still present for one release: `/api/goals` alias, response `goal_id`
mirror; `planner.generate_plan` → `run_stage3`. Follow-ups (not Active):
drop aliases; rename display field `goal`; mass-rename Python symbols
(`create_goal`, …); optionally split `planner.py` facade.

Facts: `docs/04-current-state.md` § Vocabulary / § 1; Parallel P3 / P9.

## Queue

Every known gap, bug, or unbuilt piece identified so far, numbered for
a quick count. Each points back to where the actual reasoning lives
(`docs/04-current-state.md` unless noted) rather than repeating it
here; update that file first when something changes, then this list
if the item's status changes too.

Each item carries two tags: what kind of thing it is, and roughly how
much it matters for moving the actual, working product forward right
now (not effort, not urgency in the "on fire" sense - impact):

- **Bug** - something behaves wrong today, against its own intent. **Step** - nothing is broken; the thing just doesn't exist yet. **Question** - not code at all; a design decision nothing has been built toward either way.
- **Tier 1** - small, contained, causing actually-wrong behavior today. **Tier 2** - contained, low-risk, finishes something already mostly built. **Tier 3** - already-built code, just not wired in. **Tier 4** - a new, large domain - its own multi-day round, not a quick next step. **Untiered** - a pure decision; no code is waiting on it either way, so it isn't "next" in the same sense as the others.

Ordered by tier, not by the number itself - the number is this item's
stable identity (for referring back to it), not its rank.

### Tier 1

1. ~~**`clarification`+`now` leak**~~ (fixed 2026-09-16) - Stage 3 Decide/Fill split: ASK never fills horizons. § 5.
2. **Accepting a `suggested_action` never produces a step tree** (Bug) - the acceptance branch sets `now` directly, never calls `generate_structure()`. § 5.
3. **Topic continuity / multi-goal free conversation** (Bug) - `cli.py`'s `ChatFocus` holds one goal only, and nothing detects a mid-conversation topic switch. Largest of the Tier 1 items - discussed as roughly comparable in size to a full session's own work, not a quick fix. § 5, § 9, § 10.
20. ~~**Opening gate is a duration proxy**~~ (narrowed 2026-09-17) - opening still refuses `suggested_action`; missing timeframe no longer blocks planable mint or progression click-zoom (soft grounding). Residual: planability_slots still unread; Steps scratch zoom still needs a span. § 5.
21. **Week/day calendar baseline (was: session tree painted across a longer span)** (Step residual) — **Baseline established 2026-09-16:** `week_windows()` + consecutive `day_windows()`; live-verified (#26: four real weeks). Unread `plan_skeleton` recipe removed 2026-09-20 (rules live in Time + `when/calendar.py`). Still open: year face if needed; later **ambient timeline** on the visual/do edge. Session path unchanged for short spans. § 5. Related to 17.

### Tier 2

4. **Vision choice at goal-creation time** (Step) - Set Goal and free conversation always create a goal unlinked; linking only happens afterward via Active. § 5, § 10.
5. **Structured step-completion signal** (Step) - `advance_step()` exists in `planner.py` but has no route or UI control. § 5, § 9, § 10.
6. **Vision-archive timing in the Session log** (Step) - `archive_vision()` doesn't stamp when archiving happened, only creation. § 5, § 10.
7. **Session end detection** (Step) - no graceful-shutdown hook sets a Session's real `ended_at`. Lower actual impact than the others in this tier - the read-side window-bounding fix already makes the derived log accurate without it. § 5, § 10.
12. **Decomposition / zoom, for real plans** (Step) - WHAT `plan.progression` is user-steered and is the display SoT (`to_planning_node`, A3); Projects select / Suggest / Talk / nested +/- / chat-grounded suggest under focus persist (`edit_map`). Still open: free-text step naming without map focus, zoom-ask (16), whether to stop writing calendar `plan.steps` entirely, and any remaining data-shape questions in [[planning-model.md]]. Steps page remains scratch. § 5, § 7, § 9.
16. **Zoom cannot ask for anything** (Step) - `zoom_into()` returns children or nothing, so the third state of Minimum planability's gate (UNKNOWN and NECESSARY → ask) has no per-level equivalent; a step whose breakdown depends on something personal and unstated gets a plausible invented one instead of a question. The asking machinery already exists for goal creation (`clarification`/`suggested_action`), just not here. § 5.
24. ~~**ASCII map has no way back in**~~ (built 2026-09-19) - `parse_outline.py` parses a pasted outline/ASCII tree into `import_progression_outline()`'s append. Projects' **Paste structure** form calls it. § 1.i / § 4.

### Tier 3

8. **Module Library unwired** (Step) - five working Modules, reachable from nothing. § 5.
22. **Planability slots unread** (Step) - `goal/planability_slots.py` names CONTENT/TIME/CURRENT_STATE/CAPACITY and is imported by nothing. § 5. Related to 20.

### Tier 4

9. **Node 3's second capability** (Step) - `select_capability()` can only ever return `"planning"` or `None`. § 7, § 10.
10. **Memory domain** (Step) - not built at all. § 7, § 9.
11. **Knowledge / RAG** (Step) - not built at all. § 7.
13. **Acting** (Step) - the agent performs no external action. § 7.
14. **Continuity / proactivity** (Step) - no scheduler or background behavior. § 7. Related to 17 below: for a practice, the absence of input is itself information, and nothing runs between two user messages.
25. **2D box-diagram import** (Step) - item 24's `parse_outline.py` only reads indentation-based outlines/trees (markdown bullets, numbered lists, this app's own box-drawing export). A genuine 2D box-and-arrow diagram (boxes with borders, a bracket fanning to several children, a spine continuing through only one branch) carries its structure in screen *position*, not indentation - no deterministic rule generalizes across diagram styles (arrow conventions, box characters vary). Likely path: send the pasted diagram text through `send_message()` with a JSON schema (same schema-constrained pattern `construct_progression.py` already uses), not a hand-written geometry parser - closer to a Faculty's job (interpreting ambiguous input) than deterministic code's.

### Untiered

15. **Node 1 re-voicing** (Question) - whether Node 1 should re-voice a capability's output verbatim or in its own words is undecided. § 9; see also `docs/03-architecture.md` Part 3 § 8.
17. **Practices have no shape** (Question) - a recurring, open-ended commitment ("save 10 a day", "10 push-ups a day") fits the implemented model on no axis: no deadline to count down toward, no completion to reach, nothing to decompose - a rate and an accumulation instead. Whether it's a third kind of record, a Goal with different fields, or not a Goal at all is undecided. `docs/concepts.md` § 4.ix.
18. **A plan can only be regenerated, never edited** (Question) - `step_status` is parallel-indexed to `steps`, so identity is positional and reorganizing silently moves statuses onto different steps; `current_step` is forward-only, so "2 is done but 1 isn't" is unexpressible. `replan()` regenerates; nothing edits. User **+** / **×** on `plan.progression` (2026-09-17) is a partial exception for the WHAT line only. `docs/concepts.md` § 4.x.
19. **Vision as a typing mechanism, or as background context** (Question) - whether a Vision decides what counts as progress for everything under it, or stays the weak background context `judgment/prompts.py` (`FILL_SYSTEM_PROMPT`) currently instructs it to be ("never let it override... what the goal itself actually asks for"). The two readings can't both hold. `docs/concepts.md` § 4.xi.
23. **Goal → Project product migration** (Step / Question) - UI shell is Projects; backend/prompts still Goal-planner. Thin first slice is **Active** above. Residual after that: `02-product` / concepts language; stop auto-minting a full middle without user accept; End pole = done not title; storage rename last. § 5 / § 9.

## Parallel paths

Not a second Queue — a living checklist of code that exists **twice**
or **side by side**, so we notice when something marked redundant is
used again, and so dual paths do not silently accumulate.

**Anti-mess rule (Goal → Project and any other migration):** dual code
is allowed; **unnamed** dual code is not. Before finishing a session
that adds or leans on a second path beside an old one:

1. Add or update a row in this table (status honest: Intentional dual /
   Unfinished migration / …).
2. Do **not** grow a second undocumented planner, UI home, or SoT
   “just for now.”
3. Prefer retiring or narrowing an old path over stacking a new one.
4. Detail and reasoning stay in `docs/04-current-state.md` § 5 — this
   table is the scannable ledger only.

We will not know every keep/delete up front; we **will** know every
active pair. That is how the base stays manageable.

Status meanings:

- **Intentional dual** — both needed for now (different grains). Do not delete.
- **Unfinished migration** — new shape exists; old still serves real goals. Consolidate when decided.
- **Unread / unwired** — built, nothing calls it.
- **Frozen reference** — keep for lookup; do not extend.
- **Proxy** — temporary stand-in for a fuller rule.

Update this table when a path is deleted, rewired, or reclassified.
Detail and reasoning: `docs/04-current-state.md` § 5 (Parallel / dual paths).

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Intentional dual | `when/calendar.py`, `week_windows()`, `day_windows()` |
| P2 | Even-slice `step_plan` vs dates on the step | Both live | `frozen_duration.step_plan`, manifestation |
| P3 | `plan.progression` vs legacy `plan.steps` + zoom scratch | Intentional dual (display SoT settled) | Display = progression only (`to_planning_node`, A3 2026-09-20); calendar `plan.steps` still written when fill works (WHEN); Steps page scratch — Queue 12; [[goal-to-project-migration]] A3 |
| P4 | `planability_slots` vs `_planability()` | Unread / unwired | `goal/planability_slots.py` — Queue 22 |
| P5 | Opening duration-proxy vs necessity test | Proxy (narrowed) | Missing time no longer blocks PLAN/zoom; End clarity still Decide — Queue 20 |
| P6 | `ui/` vs `frontend-legacy/` | ~~Deleted~~ | `frontend-legacy/` removed 2026-09-19 — only `ui/` remains |
| P7 | Module Library vs callers | Unread / unwired | `module_library/` — Queue 8 |
| P8 | Projects workspace vs Active (legacy) | ~~Deleted~~ | Active UI removed 2026-09-19; Projects is the only known-context surface |
| P9 | Agent auto-`construct_progression` vs user-steered map | ~~Retired~~ (A2) | `generate_plan` no longer calls `construct_progression` on PLAN (2026-09-19); middle via + / Paste / Suggest — [[goal-to-project-migration]] A2 |
