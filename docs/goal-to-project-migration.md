# Goal → Project migration

Phased product-then-wire plan for finishing the Goal → Project shift.
Folders and vocabulary are already in place ([[05-decisions]] #26 / #28);
this document tracks what is still left to change in behavior and on
the wire.

Settled product direction: [[05-decisions]] #25. Active work ledger:
`TODO.md` Active 23. Snapshot of today: [[04-current-state]].

This is **not** [[v4-migration-decision]] (LLM1 / LLM2 / LLM3) — that
architecture is largely already built; leave that file as history.

## Contents

- Status
- Phase A — product (wire unchanged)
- Gate before Phase B
- Phase B — wire / storage (done, alias period)
- Engine layout follow-up (2026-09-20)
- Out of scope
- Recommended order

## Status

**Phase A + Phase B (compat) complete** (2026-09-20). Primary wire is
`project_id` / `/api/projects`; `/api/goals` and response `goal_id` are
deprecated aliases for one release ([[05-decisions]] #29). Engine layout
the same day: `engine/plan/` flattened to `engine/judgment/` +
`engine/when/`; `planner.generate_plan` aliases `run_stage3`. Follow-ups:
drop aliases; rename display field `goal` and Python symbols; optionally
split `planner.py` facade / stop writing unused horizon keys.

| Phase | Goal | Status |
|---|---|---|
| A1 | FILL / REPLAN prompts → project / map language | **Done** 2026-09-19 |
| A2 | Stop auto-minting 2–4 middle beads on PLAN (P9) | **Done** 2026-09-19 |
| A3 | Name `plan.progression` as display SoT; keep calendar `plan.steps` as legacy WHEN (P3) | **Done** 2026-09-20 |
| A4 | Bring [[02-product]] in line with #25 + Projects home | **Done** 2026-09-20 |
| B | `project_id` / `/api/projects` / JSONL / llm3 `"project"` | **Done** 2026-09-20 (alias period) |

## Phase A — product (wire unchanged)

**Rule:** `goal_id`, `/api/goals`, and JSONL field names stay. UI and
docs may say Project.

### A1 — Engine language

Update `FILL_SYSTEM_PROMPT` and `REPLAN_SYSTEM_PROMPT` in
`app/backend/project/engine/judgment/prompts.py` to the same
**project / map** language Decide and opening already use (2026-09-18).
Confirm ASK / SUGGEST / PLAN still parse (live or planner tests).
Update [[04-current-state]] where it still says Fill/REPLAN are
Goal-flavored.

**Exit A1:** ordinary engine turns do not speak Goal-syllabus language.

### A2 — User steers the middle (narrow P9)

Today PLAN still calls `construct_first_map` (2–4 coarse phases), which
fights “user steers” (#25).

**Chosen direction:** on PLAN, do **not** auto-fill 2–4 children. Keep
root / empty progression (or a single End bead if that is already the
contract). Middle comes from user `+` / Paste / Suggest / chat-grounded
suggest.

Change the call site in the engine (`generate_plan` / lifecycle). When
verified in UI, update Parallel **P9** in `TODO.md`.

**Exit A2:** a new Project after PLAN has no agent-dumped middle line
before the user asks for one.

### A3 — `plan.progression` as display SoT (narrow P3)

`to_planning_node` already prefers progression. Do **not** delete
calendar `plan.steps` in this phase — mark them explicitly as WHEN
side-effect / legacy in [[04-current-state]] and Parallel P3. Stop
showing `plan.steps` anywhere Projects cares about, if any remain.
Calendar fill (`calendar`) may soft-fail as today — must not
block WHAT.

**Exit A3:** Projects / chat tree = progression only; the dual path is
named, not confusing.

### A4 — Product document

Update [[02-product]] so it mirrors #25 and Projects as home (not the
old goal → approve → today’s action draft flow as the main story).

**Exit A4:** Active 23’s “Still open: 02-product” can close.

**Exit Phase A (whole):** Active 23 can be marked done **without** a
wire rename. Product feel = co-build a map, not a Goal planner with a
new skin.

## Gate before Phase B

Start B only when:

- A1–A4 are done (or deliberately parked with a Parallel-paths row).
- Projects has been used for a while without missing Goal wording in
  agent replies.
- One person owns the rename window (many call sites: `goal_id`,
  `/api/goals`).

## Phase B — wire / storage

**Status: Done (compat release) 2026-09-20** — see [[05-decisions]] #29.

Primary paths are `project_id` and `/api/projects`. Exit criterion for
*removing* aliases: no `/api/goals` handlers and no `goal_id` in API
JSON (separate cleanup). Display field `goal` and Python symbols like
`create_goal` remain until a follow-up.

### B1 — Inventory + strategy

Done: compatibility layer — read both on load; write `project_id`;
alias `/api/goals` → same handlers.

### B2 — Data

Done: `_normalize_project_ids` + rewrite `plans.jsonl` when any line
still had `goal_id`.

### B3 — Agent stub

Done: llm3 asks for `"project"`; accepts legacy `"planning"`.

### B4 — Docs

Done: Vocabulary in [[04-current-state]], decision #29, this status
table, `TODO.md` Active 23.

## Engine layout follow-up (2026-09-20)

Done the same day as Phase B compat (not a numbered Phase C):

- Flattened `engine/plan/` → `engine/judgment/` + `engine/when/`
- Renamed Stage 3 modules to plain names (`decide`, `run_stage3`,
  `prompts`, `shape`, `ask`, `current_time`; calendar fill =
  `when/calendar.py`)
- Deleted unread `plan_skeleton.py` (ambient timeline noted on Queue 21)
- `planner.generate_plan` remains an alias for `run_stage3`

## Out of scope

- Module Library wiring (`TODO.md` Queue 8)
- Topic continuity / multi-goal free conversation (Queue 3)
- Zoom-ask (Queue 16)
- Year grain / ambient timeline (WHEN on the visual edge)
- Gathering chat ↔ tree UI into one module (declined)
- Mass rewrite of historical `06-development` or [[v4-migration-decision]]

## Recommended order

After this document exists: **A1** (prompts) → **A2** (auto-mint) →
**A4** (`02-product`) → **A3** (SoT clarity) → pause → **B** when the
gate is true.

## See also

- [[05-decisions]] #25, #26, #28
- [[04-current-state]] § Vocabulary, § 5 Parallel paths
- `TODO.md` Active 23, Parallel P3 / P9
