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

1. **User / id** — clean up simulated users (`id#N` / Manager /
   `sim_user_id`): what an “id” is in the product, rename (26), default
   project names on the server (29), how this maps later to real accounts
   ([[02-product]] § 5). This is the real focus, not more map/chat.
2. **`architecture_foundation/`** — decide keep-as-archive vs move vs
   delete; do **not** rewrite it to match Map+Talk (it’s the old
   agent-shape sketch). See Queue 43.
3. **Docs north star** — keep **02 / 04 / 05** current; demote or stamp
   outdated **00 / 03** (and closed **06**) so sessions don’t relearn
   the planner-agent story. Light pass, not a full rewrite.

Related to 26, 29, 27, 43. Time Faculty files can stay unused (21).

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
26. **Id has no rename** (Step) — create and delete exist; no way to
    change an id's label after creation. § 1.i.
29. **Default project names are decided in the UI** (Step) — "New
    project N" lives in `defaultNames.ts`; move into `create_project()`
    when the name is empty so other clients share it. § 1.i.
30. **No written API reference** (Step) — short overview of each
    `/api/...` address. `docs/02-product.md` § 5.

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
