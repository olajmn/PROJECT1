# TODO

Not a duplicate of `docs/04-current-state.md` - that file is the full,
factual account of what's true now, including known bugs/gaps and the
reasoning behind each. This file only tracks which of those are
actually being worked on (**Active**), a numbered catalog of
everything still open (**Queue**), and a **Parallel paths** table of
dual/redundant code — so scope and active pairs stay visible at a
glance.

Done / removed Stage-3 and old-plan items are **not** kept here;
their history lives in `docs/04-current-state.md` and
`docs/05-decisions.md`. An item moves from Queue to Active only when
deliberately chosen as next.

## Active

**42. Pre-demo clean box** (Step, next) — Map+Talk (40) is done enough
to demo the loop; this is what’s left before calling it demo-ready.

1. ~~**User / account**~~ — done 2026-09-26 (accounts, Directory,
   Archive, server-side default names; what exists: `docs/04-current-state.md`
   § 1). Real accounts / wallets are not pre-demo — they come from the
   NFT app ([[02-product]] § 5).
2. **`architecture_foundation/`** — decide keep-as-archive vs move vs
   delete; do **not** rewrite it to match Map+Talk (it’s the old
   agent-shape sketch). See Queue 43.
3. **Docs north star** — keep **02 / 04 / 05** current; demote or stamp
   outdated **00 / 03** (and closed **06**) so sessions don’t relearn
   the planner-agent story. Light pass, not a full rewrite.

Related to 27, 43. Time Faculty files can stay unused (21).

## Queue

Each item: kind (**Bug** / **Step** / **Question**) and impact tier
(**1** wrong today → **4** large new domain; **Untiered** = design
only). Numbers are stable ids, not rank. Detail stays in `docs/04`
unless noted.

### Tier 1

21. **Week/day calendar baseline** (Step, parked) — Time can still
    compute `week_windows()` / `day_windows()`, but nothing in the
    product calls them since project calendar fill was removed. Only
    relevant if time returns to the map (year face, ambient timeline).
    § 5. Related to 17, 27.

### Tier 2

12. **Decomposition / zoom** (Step) — map is user-steered
    (`plan.progression`); + / × / Paste / Add folder / Suggest /
    chat-suggest under a selected node write it. Still open: naming a
    node in chat without selecting it first, and remaining data-shape
    questions in [[planning-model.md]]. § 5, § 7, § 9.
30. **No written API reference** (Step) — short overview of each
    `/api/...` address. `docs/02-product.md` § 5.
44. **Repo cleanup pass** (Step) — findings from a file review on
    2026-09-26 (`tools.project_check` + spot reads). Items already
    tracked elsewhere are only cross-referenced: `architecture_foundation/`
    (43), outdated 00 / 03 (Active 42.3), unused Time Faculty (21),
    Status vs Current state naming (37), API reference (30).

    **Weight and order.** Most items are docs (2, 3, 8, 9 + 42.3, 43):
    many, light, text-only — one session. The code items are few but
    heavier: **5** is the main one (storage, follow `test_storage`
    closely); Time Faculty (21, ~1 360 unused lines) is a keep-or-remove
    decision, not cleanup; **6** and **7** are not urgent; **4** is a
    one-minute fix. The code itself is in good shape (pyflakes clean,
    small files) — the mess is mostly docs still telling the old
    planner-agent story. Order: docs first, then 5.

    1. ~~**`docs/04-current-state.md` lags the last commits**~~ — done
       2026-09-26 (default names, never-reused account ids).
    2. **Stale code paths in living docs** — `docs/03-architecture.md:191`
       and `docs/04-current-state.md:119` (`backend/llm_client.py`),
       `docs/04-current-state.md:336` (`backend/goals/plan/action_reader.py`).
       Hits in 05 / 06 / `v4-migration-decision.md` are history and
       can stay.
    3. **Working notes in `docs/`** — decide done (archive), active, or
       merge into 02 / 04 for `v4-migration-decision.md`,
       `goal-to-project-migration.md` (still points at "TODO Active
       23", which no longer exists), `visual-reset.md`, `surfaces.md`.
    4. **`app/ui/dist/api.js` is tracked although `app/ui/dist/` is in
       `.gitignore`** — still changes in commits. Untrack with
       `git rm --cached` or adjust the ignore rule.
    5. **Legacy Goal code in storage** — `project_persistence.py` (740
       lines, largest file) carries old-format normalization /
       migration (`_backfill_goal_ids`, `_next_goal_id`,
       `_migrate_legacy_snapshot_file`, …); `goal_id` still appears
       ~26 times in backend + UI as the deprecated mirror of
       `project_id`. Split migration into its own module, or drop it
       once old data is converted.
    6. **`requests_from_browser.py` routing** — one long `if/elif` on
       `self.path` per method (445 lines); grows with every endpoint.
       Not urgent. Related to 30.
    7. **Test gaps** — no tests for `requests_from_browser.py`,
       `edit_map.py`, or any UI TypeScript.
    8. **`README.md` is 6 lines** — enough for solo use; needs more
       before anyone else (or the NFT app) joins.
    9. **`docs_lint` review hits** — 4 "the user's own …" phrases
       (`CONVENTIONS.md:29`, `docs/05-decisions.md:84` / `:105`,
       `docs/concepts.md:205`); check by hand.
45. **Copy one branch as ASCII** (Step, after cleanup) — Copy as ASCII
    (`panes/canvas/copyAsText.ts`) always copies the whole tree. Add
    either a **Copy branch** item in the node ⋯ menu, or let Copy as
    ASCII copy only the selected node's subtree when one is selected.
    Not a chat `/` command: a dump in the thread is noise, and the
    thread goes back to the model — same reason Print map was dropped
    ([[05-decisions]] #48).
46. **Talk demo polish** (Step, pre-demo candidate for Active 42) —
    answers feel weak today. Bounded pass so chat reads as a working,
    deliberate part of the product, not a prototype.
    1. **Analyse first** — why answers are poor, above all what the
       model actually receives as context (brief, focus node, history);
       explain the problem briefly before larger changes.
    2. **Then fix only what's needed:** relevant answers about the
       project; clear context for the selected project / node; natural,
       readable thread; tidy loading / error states; input + Send work;
       existing slash-commands (`panes/chat/commands/`) keep working.
    3. **4–5 demo scenarios** the chat should handle, written down.
    Out of scope: RAG, long-term memory, agent loops, new chat
    architecture. Related to 33 (model sees only labels).
48. **Rename `sim_user_id` → `account_id`** (Step, before Saved Trees
    if possible) — the store is already `accounts`, but a project's
    account reference is still `sim_user_id` ([[05-decisions]]
    accounts-store follow-up: "Project FK stays `sim_user_id`").
    Scope checked 2026-09-27: 138 occurrences in 21 code files
    (backend storage/api/create + UI `dataShapes.ts`, `api.ts`,
    accounts panel, Directory), the wire (`POST /api/projects/<id>/user`
    body), 15 doc mentions. Data: 47 projects carry it in
    `current.json` / `events.jsonl`, and every saved tree carries it in
    `data/saved_trees.json` (added 2026-09-27) — promote `sim_user_id` →
    `account_id` on load rather than rewriting files; new saves write
    only `account_id`. Backend and UI change together. Dated history
    in `05-decisions.md` keeps the old name; record the rename as a new
    decision.
49. **A proper way to check node ids** (Step, shape open) — node ids
    are identity ([[05-decisions]] #52) and never reused (`node_id_hi`),
    but nothing lets you see or verify them. Candidates:
    1. **Inspect:** partly done — Talk `/id` shows the selected node's
       id or switches the map to ids ([[05-decisions]] #55). Still
       open: a flat overview of every node (Settings → Nodes: project,
       id, label, parent, depth), like Directory shows Local # +
       Global ID.
    2. **Verify:** a check (e.g. in `tools/project_check.py` or a test)
       that walks `data/projects/*/current.json` and reports duplicate
       ids in one tree, ids above `node_id_hi`, and `focus_step_id` on
       events pointing at an id that never existed.
    Rules live in `app/backend/project/node/README.md`.
50. **Node ids → globally unique random ids** (Step, before NFT merge,
    not during mockup) — `p<N>` ids are sequential and unique per
    project only: they collide when data from several projects,
    devices, or the NFT app is merged, need one counter
    (`node_id_hi`), and leak count/order. Target: **UUIDv7** or
    **ULID** (128 bit: no practical collisions, time-sortable, no
    counter; fits a `uint256` ERC-721 token id). Not short random
    digits: 7 digits (10^7) reach ~50 % collision odds at ~3,700 ids.
    1. Identity stays separate from content (#52): the id is random and
       stable; a hash of structure can serve as a fingerprint (e.g. a
       saved tree to mint), never as the id.
    2. Display a short prefix (6–8 chars, like git); addressing by
       prefix must be unique within the project.
    3. Single change point is `_id_minter()` (`edit_map.py`); old `p`
       ids referenced by `focus_step_id` in `events.jsonl` need a
       transition (keep them, or map old → new). `node_id_hi` becomes
       unnecessary.
    4. Open question: which side mints node identity once the NFT app
       joins ([[02-product]] § 5 — data comes from outside via API).
       Only roots/fingerprints on chain, not every node (gas cost).
51. **Saved trees follow-ups** (Step, when needed) — built 2026-09-27
    ([[05-decisions]] #54). Open:
    1. Rename a saved tree (name is the node label at save time).
    2. A library view outside the picker (list, rename, delete), e.g.
       under Settings or the account.
    3. Unassigned projects (`sim_user_id` null) share one library.
    4. `source` ({project_id, step_id}) is provenance only; a
       cross-project identity / fingerprint for minting belongs with
       Queue 50.

### Tier 4

9. **A second capability** (Step) — agent can only do Project today.
   Design in `docs/03-architecture.md`. § 7.
10. **Memory domain** (Step) — not built. § 7, § 9.
11. **Knowledge / RAG** (Step) — not built. § 7.
13. **Acting** (Step) — no external action. § 7.
14. **Continuity / proactivity** (Step) — no scheduler / background
    behavior. § 7. Related to 17.
25. **2D box-diagram import** (Step) — paste today is indentation /
    outline only (`text_to_tree.py`); true 2D box diagrams need a
    different path (likely schema-constrained model read). § —

### Untiered

17. **Practices have no shape** (Question) — recurring open-ended
    commitments ("10 push-ups a day") fit no current axis. `docs/concepts.md`
    § 4.ix.
27. **What counts as a session / visit** (Question) — if the agent
    should understand time-with-the-user, build on `created_at` in
    project history / Logs, not server starts. § 5.
33. **Talk only sees the map's labels** (Question) — model gets labels
    + focus path, not file contents / notes behind a node. [[05-decisions]]
    #33.
37. **Rename Status code to Current state** (Step, not crucial) —
    UI says "Current state"; folders/`status` wire/`build_status` still
    say Status. Optional later (avoid confusing with disk `current.json`).
    Related to 34.
38. **Click a Changes day → map + chat focus** (Step, parked) —
    highlight nodes touched that day; isolate talk about those changes
    (like node About). Needs richer event payload. Related to 34.
39. **Talk commands that force a SoT pass** (Step, keep in mind) —
    e.g. a chat "full check" that deliberately re-reads `current` (+
    events) — the product twin of Cursor `/full-check`, for the *user
    project* not this repo. Current state panel is mainly for the human;
    the model already gets a slice via `status_text`, but explicit
    commands are optional later. Lives under `panes/chat/commands/`
    when built. Related to model brief (#42 in decisions; was Active 40).
41. **Delete a node with children** (Question) — today × removes the
    whole subtree (cascade). Fine while trees are shallow; later may
    want promote children, forbid-until-empty, or ask. Tree policy
    (owned with `project/node/`), not only canvas chrome — same rule
    should apply if Talk ever deletes. Related to 12, 40.
43. **`architecture_foundation/` disposition** (Question) — root folder
    is a historical full-agent skeleton (Vision/Goal/Plan/…); not the
    Map+Talk product. Useful later as archaeology or when a *new*
    multi-app map is needed (e.g. NFT entrance); wrong as current
    target. Options: leave + stamp “historical”, move under `docs/` /
    archive, or delete. Do not rebuild it to mirror `app/` before demo.
    In Active 42. Related to outdated [[03-architecture]].

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified. Detail:
`docs/04-current-state.md` § 5.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 21 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; map does not read leftover `plan.steps` |
| P3 | `plan.progression` vs legacy `plan.steps` | Leftover on disk only | Screen draws `progression` only; older records may still carry `steps` |
