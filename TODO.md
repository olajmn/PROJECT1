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

UX problems found in use, taken before the wider UI/UX pass.

53. **`/select` needs the full path and exact name** (Step, tier 2) —
    `/select 1. Planning` fails when it sits under another node, and a
    typo fails without a hint. Candidates: find a unique name anywhere
    in the tree, ignore case, suggest the closest name. Rules in
    `panes/chat/commands/node_path.py`. Split out of 12.

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

    4. **`app/ui/dist/api.js` is tracked although `app/ui/dist/` is in
       `.gitignore`** — still changes in commits. Untrack with
       `git rm --cached` or adjust the ignore rule. One-minute fix.
    6. **`requests_from_browser.py` routing** — one long `if/elif` on
       `self.path` per method; grows with every endpoint. Not urgent.
       Related to 30.
    7. **Test gaps** — no tests for `requests_from_browser.py`,
       `edit_map.py` on its own, or any UI TypeScript.
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
    import text ("Imported 1 step(s) under X" does not say what; added
    and removed steps already say what and where). Related to 34.
39. **Talk commands that force a SoT pass** (Step, keep in mind) —
    e.g. a chat "full check" that deliberately re-reads `current` (+
    events) — the product twin of Cursor `/full-check`, for the *user
    project* not this repo. Current state panel is mainly for the human;
    the model already gets a slice via `status_text`, but explicit
    commands are optional later. Lives under `panes/chat/commands/`
    when built. Related to model brief (#42 in decisions; was Active 40).

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

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 21 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; nothing in the product calls it |
| P4 | Tree as text: indented labels vs ASCII tree | Deliberate, one per side | `project/node/tree_as_text.py` (`tree_lines()`, for the model) vs `ui/src/panes/canvas/copyAsText.ts` (clipboard); same walk, the model side cannot run in the browser and the clipboard should not need a server round trip |
| P5 | Event kind → word: Logs titles vs day tally | Deliberate, different grain | `project/timeline.py` `GROUPS` ("Map") vs `project/status/build_status.py` `_TALLY_WORDS` ("added", "removed", "imported"); a new event type goes in both, or it shows as Other / other |
