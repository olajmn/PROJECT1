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
- Phase B — wire / storage (parked until gate)
- Out of scope
- Recommended order

## Status

**Phase A complete** (A1–A4 done 2026-09-19/20). Wire still uses
`goal_id` / `/api/goals` on purpose. Do not start Phase B until the
gate below is true.

| Phase | Goal | Status |
|---|---|---|
| A1 | FILL / REPLAN prompts → project / map language | **Done** 2026-09-19 |
| A2 | Stop auto-minting 2–4 middle beads on PLAN (P9) | **Done** 2026-09-19 |
| A3 | Name `plan.progression` as display SoT; keep calendar `plan.steps` as legacy WHEN (P3) | **Done** 2026-09-20 |
| A4 | Bring [[02-product]] in line with #25 + Projects home | **Done** 2026-09-20 |
| B | `project_id` / `/api/projects` / JSONL / llm3 `"project"` | Parked |

## Phase A — product (wire unchanged)

**Rule:** `goal_id`, `/api/goals`, and JSONL field names stay. UI and
docs may say Project.

### A1 — Engine language

Update `FILL_SYSTEM_PROMPT` and `REPLAN_SYSTEM_PROMPT` in
`app/backend/project/engine/plan/plan_prompts.py` to the same
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
Calendar fill (`plan_structure`) may soft-fail as today — must not
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

## Phase B — wire / storage (parked until gate)

**Goal:** `project_id`, `/api/projects`, JSONL fields, llm3 `"project"`
— without changing product rules.

### B1 — Inventory + strategy

Count call sites in `app/backend/store/data_persistence.py`,
`app/backend/api/routes.py`, `app/ui/src/api.ts`, types, tests.

**Chosen strategy:** one-release compatibility layer — read both
`goal_id` and `project_id`; write `project_id`; alias old URLs to
`/api/projects`. Then remove the alias.

### B2 — Data

Migrate `plans.jsonl` field names (or keep a permanent read alias).
Update session / chat-focus fields that point at a goal id.

### B3 — Agent stub

`app/backend/agent/llm3/select.py`: `"planning"` → `"project"` (accept
both temporarily).

### B4 — Docs

Update Vocabulary in [[04-current-state]]: “wire still goal_id” → done.
Add decision #29 in [[05-decisions]] when B lands.

**Exit Phase B:** no `/api/goals` or `goal_id` in live paths (tests +
UI + store).

## Out of scope

- Module Library wiring (`TODO.md` Queue 8)
- Topic continuity / multi-goal free conversation (Queue 3)
- Zoom-ask (Queue 16)
- Year grain / `plan_skeleton` wiring
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
