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

**23. Goal → Project migration** (~~Phase A + B + alias drop done~~ 2026-09-20)

Product [[05-decisions]] #25; wire [[05-decisions]] #29 /
[[goal-to-project-migration]]. Primary only: `project_id`, `/api/projects`,
llm3 `"project"`. Decide/Fill engine is gone. Still open (not Active):
rename display field `goal`; mass-rename Python symbols (`create_goal`,
…).

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
2. ~~**Accepting a `suggested_action` never produces a step tree**~~ (removed with `route_note` / judgment). § 5.
3. ~~**Topic continuity / multi-goal free conversation**~~ (removed 2026-09-20) — free conversation / `ChatFocus` / CLI / Node 3 deleted (#31). Projects chat is keyed by URL id. § 5.
20. ~~**Opening gate is a duration proxy**~~ (narrowed 2026-09-17) - opening still refuses `suggested_action`; missing timeframe no longer blocks planable mint or progression click-zoom (soft grounding). Residual: planability_slots still unread; Steps scratch zoom still needs a span. § 5.
21. **Week/day calendar baseline (was: session tree painted across a longer span)** (Step residual) — Time still has `week_windows()` / `day_windows()`. Project calendar fill (`engine/time/calendar.py`) is gone. Still open: year face if needed; later **ambient timeline**. § 5. Related to 17.

### Tier 2

4. **Sim-user choice at project-creation time** (Step) - Set Goal always creates a project unlinked; linking only happens afterward via Projects sidebar id menu. § 5, § 10.
5. **Structured step-completion signal** (Step) - `advance_step()` is gone with the planner; no live writer for step status. § 5, § 9, § 10.
6. **User-archive timing** (Step) - `archive_user()` doesn't stamp when archiving happened, only creation. § 5, § 10.
7. ~~**Session end detection**~~ (moot 2026-09-25) - Sessions removed ([[05-decisions]] #35). See 27.
12. **Decomposition / zoom, for real plans** (Step) - WHAT `plan.progression` is user-steered and is the display SoT (`map_tree()`, A3); Projects select / Suggest / Talk / nested +/- / chat-grounded suggest under focus persist (`edit_map`). Still open: free-text step naming without map focus, zoom-ask (16), whether to stop writing calendar `plan.steps` entirely, and any remaining data-shape questions in [[planning-model.md]]. Steps page remains scratch. § 5, § 7, § 9.
16. **Zoom cannot ask for anything** (Step) - `zoom_into()` returns children or nothing, so the third state of Minimum planability's gate (UNKNOWN and NECESSARY → ask) has no per-level equivalent; a step whose breakdown depends on something personal and unstated gets a plausible invented one instead of a question. The old asking machinery (`clarification`/`suggested_action`) is gone with Stage 3. § 5.
24. ~~**ASCII map has no way back in**~~ (built 2026-09-19) - `parse_outline.py` parses a pasted outline/ASCII tree into `import_progression_outline()`'s append. Projects' **Paste structure** form calls it. § 1.i / § 4.
26. **Id has no rename** (Step) - create (`buildCreateIdForm`, one-click "+" since 2026-09-22) and delete (`sidebar-id-card-menu` "Delete") both exist; there's no way to change an id's label after creation short of delete + recreate. Noted live when the create flow was simplified to drop its label input. § 1.i.

### Tier 3

8. ~~**Module Library unwired**~~ (removed 2026-09-25, [[05-decisions]] #34) - code deleted; design stays in `docs/03-architecture.md` Part 2 § 2.ii.
22. ~~**Planability slots unread**~~ (removed). § 5. Related to 20.

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
27. **What counts as a session / visit** (Question) - the removed Session record (#35) meant a server process start, not a user visit. If the agent should understand time (when the user was last here, cadence of contact), a visit likely builds on the timestamps every saved chat turn and map change already carries (`created_at` in `plans.jsonl`), not on server starts. Settings → Logs already lists those timestamps (`activity_log()`). § 5.
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
| P1 | Week grain vs session grain | Intentional dual | `time/calendar.py`, `week_windows()`, `day_windows()` |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; manifestation no longer maps leftover `plan.steps` |
| P3 | `plan.progression` vs legacy `plan.steps` + zoom scratch | Intentional dual (display SoT settled) | Display = progression only (`map_tree()`, A3 2026-09-20); calendar `plan.steps` still written when fill works (WHEN); Steps page scratch — Queue 12; [[goal-to-project-migration]] A3 |
| P4 | `planability_slots` vs `_planability()` | Unread / unwired | `goal/planability_slots.py` — Queue 22 |
| P5 | Opening duration-proxy vs necessity test | Proxy (narrowed) | Missing time no longer blocks PLAN/zoom; End clarity still Decide — Queue 20 |
| P6 | `ui/` vs `frontend-legacy/` | ~~Deleted~~ | `frontend-legacy/` removed 2026-09-19 — only `ui/` remains |
| P7 | Module Library vs callers | ~~Deleted~~ | `module_library/` removed 2026-09-25 (#34) — Queue 8 |
| P8 | Projects workspace vs Active (legacy) | ~~Deleted~~ | Active UI removed 2026-09-19; Projects is the only known-context surface |
| P9 | Agent auto-`construct_progression` vs user-steered map | ~~Retired~~ (A2) | Helper file deleted; middle via + / Paste / Suggest |
