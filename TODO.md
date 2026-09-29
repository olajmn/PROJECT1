# TODO

Not a duplicate of `docs/04-current-state.md` - that file is a short
snapshot of what's true now, including known limits. This file only
tracks which of those are
actually being worked on (**Active**), a numbered catalog of
everything still open (**Queue**), and a **Parallel paths** table of
dual/redundant code — so scope and active pairs stay visible at a
glance.

Done / removed Stage-3 and old-plan items are **not** kept here;
their history lives in `docs/05-decisions.md` and git history. An
item moves from Queue to Active only when
deliberately chosen as next.

## Active

The UI/UX pass, starting with real content to design against.

55. **Realistic demo projects** (Step, first) — the saved data is test
    content ("ggehh", "1 / 2 / 3 / 4"), which makes spacing, hierarchy,
    long names, and deep trees hard to judge. The owner builds 2–3
    projects that together show what the app is for — for example an
    event plan, a recipe, and a folder from disk — in an account of
    their own, with some changes over more than one day and a little
    Talk. They are what the UI is judged against and what a demo
    opens on. Open: whether the old test projects are archived or
    kept apart.
56. **UI/UX pass: how the screen looks** (Step) — presentation only,
    not new features: hierarchy (loud / quiet / hidden), spacing, type,
    and the look of the canvas, chat, Current state, and sidebar,
    judged against the projects from 55. Principles and layout:
    `docs/ui.md`. The main pass is done ([[05-decisions]] #68), Settings
    included; left: 57 (tree on the dot grid). Frosted glass is parked
    (§ Ideas). Items that may fold in when they come up: 53 (`/select`
    hint), 54 (undo), 45 (copy one branch), 38 (changed nodes on the
    map).

## Queue

Each item: kind (**Bug** / **Step** / **Question**) and impact tier
(**1** wrong today → **4** large new domain; **Untiered** = design
only). Numbers are stable ids, not rank.

### Tier 1

21. **Week/day calendar baseline** (Step, parked) — Time can still
    compute `week_windows()` / `day_windows()`, but nothing in the
    product calls them since project calendar fill was removed. Only
    relevant if time returns to the map (year face, ambient timeline).
    Related to 17, 27.

### Tier 2

12. **Decomposition / zoom** (Step) — map is user-steered
    (`plan.progression`); + / × / Paste / Add folder under a selected
    node write it. Naming a node in chat without the full path is
    Active 53. Model-proposed children were removed ([[05-decisions]]
    #60, #63); if they return, as an explicit `/suggest` that proposes
    in the chat and leaves adding to the user.
30. **No written API reference** (Step) — short overview of each
    `/api/...` address.
44. **Repo cleanup pass** (Step) — what is left of a file review on
    2026-09-26; the docs part was done 2026-09-27 (#57). Numbers are
    kept from the original list.

    6. **`requests_from_browser.py` routing** — POST goes through the
       `_POST_ROUTES` table, but `do_GET()` is still one `if/elif` on
       `self.path`. Not urgent. Related to 30.
    7. **Test gaps** — no tests for `requests_from_browser.py` or any
       UI TypeScript; `edit_map.py` is covered only for the saved text
       of remove, import, and move (`test_edit_map.py`).
45. **Copy one branch as ASCII** (Step, after cleanup) — Copy as ASCII
    (`panes/canvas/copyAsText.ts`) always copies the whole tree. Add
    either a **Copy branch** item in the node ⋯ menu, or let Copy as
    ASCII copy only the selected node's subtree when one is selected.
    Not a chat `/` command: a dump in the thread is noise, and the
    thread goes back to the model — same reason Print map was dropped
    ([[05-decisions]] #48).
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
50. **Node ids → globally unique random ids** (Step, before data is
    shared outside this app, not during mockup) — `p<N>` ids are
    sequential and unique per project only: they collide when data from
    several projects, devices, or another app is merged, need one
    counter (`node_id_hi`), and leak count/order. Target: **UUIDv7** or
    **ULID** (128 bit: no practical collisions, time-sortable, no
    counter). Not short random digits: 7 digits (10^7) reach ~50 %
    collision odds at ~3,700 ids.
    1. Identity stays separate from content (#52): the id is random and
       stable; a hash of structure can serve as a fingerprint (e.g. to
       show a saved tree is unchanged), never as the id.
    2. Display a short prefix (6–8 chars, like git); addressing by
       prefix must be unique within the project.
    3. Single change point is `_id_minter()` (`edit_map.py`); old `p`
       ids referenced by `focus_step_id` in `events.jsonl` need a
       transition (keep them, or map old → new). `node_id_hi` becomes
       unnecessary.
    4. Open question: which side mints node identity if another app
       shares the data.
51. **Saved trees follow-ups** (Step, when needed) — built 2026-09-27
    ([[05-decisions]] #54). Open:
    1. Rename a saved tree (name is the node label at save time).
    2. A library view outside the picker (list, rename, delete), e.g.
       under Settings or the account.
    3. Unassigned projects (`account_id` null) share one library.
    4. `source` ({project_id, step_id}) is provenance only; a
       cross-project identity belongs with Queue 50.

53. **`/select` gives no hint when it fails** (Step) — matching stays
    exact on purpose (full path from the top, exact name): a command
    that guesses could select the wrong node unnoticed. What is
    missing is a useful reply instead of "No node at path": where a
    unique name actually sits (`"1. Planning" is under BIRTHDAY PARTY
    - try /select BIRTHDAY PARTY / 1. Planning`), or the closest name
    for a typo. Clicking a node stays the main way to select. Rules in
    `panes/chat/commands/node_path.py`. Split out of 12.
54. **Undo for map edits (Ctrl+Z)** (Step) — removing a node now asks
    first when it has children (Active 41, closed), but nothing can be
    undone. Likely shape: keep the last 10–20 versions of the tree
    before each map edit (the events tape holds only short texts, not
    the tree); Undo puts the previous version back as a new saved
    change. To decide: which edits count (add, remove, paste, folder,
    insert tree, rename?), whether undo survives a reload, redo,
    Ctrl+Z only while the map has focus (text fields keep their own
    undo), and a visible Undo after a remove. With undo in place the
    remove confirmation may go. Also open from 41: removing a node but
    keeping its children (moved up a level).

### Tier 4

9. **A second capability** (Step) — the app can only do Project today.
10. **Memory domain** (Step) — not built.
11. **Knowledge / RAG** (Step) — not built.
13. **Acting** (Step) — no external action.
14. **Continuity / proactivity** (Step) — no scheduler / background
    behavior. Related to 17.
25. **2D box-diagram import** (Step) — paste today is indentation /
    outline only (`text_to_tree.py`); true 2D box diagrams need a
    different path (likely schema-constrained model read).

### Untiered

17. **Practices have no shape** (Question) — recurring open-ended
    commitments ("10 push-ups a day") fit no current axis.
27. **What counts as a session / visit** (Question) — if the agent
    should understand time-with-the-user, build on `created_at` in
    project history / Logs, not server starts.
33. **Talk only sees the map's labels** (Question) — model gets labels
    + focus path, not file contents / notes behind a node. [[05-decisions]]
    #33.
37. **Rename Status code to Current state** (Step, not crucial) —
    UI says "Current state"; folders/`status` wire/`build_status` still
    say Status. Optional later (avoid confusing with disk `current.json`).
    Related to 34.
38. **Click a Changes day → map + chat focus** (Step, parked) — the
    chat part is built ([[05-decisions]] #62): a day in Current state
    selects that day's changes for Talk, framed like node About. Still
    open: highlight the nodes touched that day on the map, and richer
    import text ("Imported 95 nodes under X" counts every node but does
    not say which; added and removed steps already say what and where).
    Related to 34.
39. **Talk commands that force a SoT pass** (Step, keep in mind) —
    e.g. a chat "full check" that deliberately re-reads `current` (+
    events) — the product twin of Cursor `/full-check`, for the *user
    project* not this repo. Current state panel is mainly for the human;
    the model already gets a slice via `status_text`, but explicit
    commands are optional later. Lives under `panes/chat/commands/`
    when built. Related to model brief (#42 in decisions; was Active 40).
57. **Line the map up with the dot grid** (Step, later) — the dot grid
    behind the map (`app/ui/css/panes/canvas/dotGrid.css`) and the tree
    are not aligned: indent and row height (`panes/canvas/spacing.ts`,
    `map.css`) are set in `rem`, independently of the dot spacing. To
    align, pick one base unit (e.g. 8–9px) and make the indent step, the
    row pitch, and the dot spacing whole multiples of it, and offset the
    grid by the viewport padding so it starts where the tree does. Easy
    first half: only the vertical spines on dot columns (the indent is
    already fixed). Does not hold below the grid's 9px minimum spacing
    (far zoomed out). Layout change, not CSS only.

## Ideas (not decided)

Not planned and not built — kept so they are not lost. Moving one into
the Queue is a deliberate choice.

- **Node types and fields** — a node could carry a type and structured
  fields, not only a label and children (cf. Tana; `docs/01-research.md`).
- **More than one parent** — letting a node sit in several places would
  turn the tree into a graph; the node model would stay, the relation
  rule would change (`docs/00-project-brief.md` § 2).
- **Export / share a structure** — a branch or project as a document or
  file others can open (Queue 45 copies one branch as ASCII).
- **Sync across devices** with end-to-end encryption, the local copy
  staying the real one (`docs/03-architecture.md` § 5).
- **Other front ends on the same data** — the node data is portable, so
  a different interface could read it.
- **Frosted glass as a material** (tried 2026-09-29, parked) — a Settings
  switch (Solid | Glass) that made the floating block, the map's top
  strip and menus translucent with a blur (block alpha 0.66, blur 48px,
  saturate 160%). Over the calm Graphite backdrop it was barely visible,
  and the tree blurring under the top strip competed with its controls.
  Worth trying again only with a livelier backdrop behind the block and
  a solid top strip; the sketch `glass-sketch.html` (git-excluded, repo
  root) still has the knobs.

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 21 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; nothing in the product calls it |
| P4 | Tree as text: indented labels vs ASCII tree | Deliberate, one per side | `project/node/tree_as_text.py` (`tree_lines()`, for the model) vs `ui/src/panes/canvas/copyAsText.ts` (clipboard); same walk, the model side cannot run in the browser and the clipboard should not need a server round trip |
| P5 | Event kind → word: Logs titles vs day tally | Deliberate, different grain | `project/timeline.py` `GROUPS` ("Map") vs `project/status/build_status.py` `_TALLY_WORDS` ("added", "removed", "imported"); a new event type goes in both, or it shows as Other / other |
