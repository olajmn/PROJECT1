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

**46. Talk demo polish** (Step, before a demo) — answers feel weak
today. Bounded pass so chat reads as a working, deliberate part of the
product, not a prototype.

1. **Analyse first** — why answers are poor, above all what the model
   actually receives as context (brief, focus node, history); explain
   the problem briefly before larger changes.
2. **Then fix only what's needed:** relevant answers about the project;
   clear context for the selected project / node; natural, readable
   thread; tidy loading / error states; input + Send work; existing
   slash-commands (`panes/chat/commands/`) keep working.
3. **4–5 demo scenarios** the chat should handle, written down.

Known model behavior to check against (old experiments on
`llama3.1:8b`): it invented plausible details never given ("chapter
11", "a friend"); Norwegian input gave answers unrelated to the
question, 3 of 3 times, while English was fine — re-test on
`qwen3.5:9b`, since the owner writes Norwegian; with only the latest
turn it drifted from the goal, and full history fixed it (Talk sends 20
turns today).

Out of scope: RAG, long-term memory, agent loops, new chat
architecture. Related to 33 (model sees only labels).

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
    (`plan.progression`); + / × / Paste / Add folder / Suggest /
    chat-suggest under a selected node write it. Still open: naming a
    node in chat without selecting it first.
30. **No written API reference** (Step) — short overview of each
    `/api/...` address.
44. **Repo cleanup pass** (Step) — what is left of a file review on
    2026-09-26; the docs part was done 2026-09-27 (#57). Numbers are
    kept from the original list.

    4. **`app/ui/dist/api.js` is tracked although `app/ui/dist/` is in
       `.gitignore`** — still changes in commits. Untrack with
       `git rm --cached` or adjust the ignore rule. One-minute fix.
    5. **Goal naming in comments** — the legacy storage code is gone
       (#56, #59); a few docstrings still say "goal" for a project
       (`panes/create/lifecycle.py`, `project_account.py`,
       `chat/screen/chat_thread.py`). Wording only.
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
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; map does not read leftover `plan.steps` |
| P3 | `plan.progression` vs legacy `plan.steps` | Leftover on disk only | Screen draws `progression` only; older records may still carry `steps` |
