# 04 — Current State

What is true in the code right now; update it in the same change that makes it untrue.

## 1. Run it

From `app/`, with its own `.venv/` (`ollama` is only installed there):

| What | Command |
|---|---|
| Start the app | `.venv/bin/python -m server` → http://localhost:8000/ |
| One test suite | `.venv/bin/python -m backend.<path>.test_<name>` |
| Build the UI | `cd ui && npm run build` (TypeScript → `ui/dist/`) |
| Project checks | from the root: `app/.venv/bin/python3 -m tools.project_check` |

`/full-check` runs the checks and every test suite in one go.

## 2. Where things are

The layers and their rules are in [[03-architecture]]. By feature:

| Feature | Backend | UI |
|---|---|---|
| Create, rename, archive, restore projects | `project/panes/create/` (`lifecycle.py`, `rename.py`) | `ui/src/panes/create/` |
| Accounts and which one owns a project | `storage/accounts_persistence.py`, `panes/create/project_account.py` | `panes/create/accounts/`, `settings/directory/` |
| What a node is; ids; sibling names | `project/node/` (see its `README.md`) | — |
| Add, remove, paste, folder, suggest | `panes/canvas/edit_map.py`, `text_to_tree.py`, `add_folder/`, `call_suggest.py` | `panes/canvas/` |
| Saved trees | `project/saved_trees/`, `storage/saved_trees_persistence.py` | `panes/canvas/savedTrees/` |
| The map as drawn | `api/answers_to_browser.py` (`map_tree()`) | `panes/canvas/drawNodes.ts`, `lines/`, `zoomAndPan/` |
| A Talk turn | `panes/chat/reply.py`, `model/brief/conversation.py`, `talk_prompt.py` | `panes/chat/` |
| Slash commands | `panes/chat/commands/` | `panes/chat/commands/` |
| The chat thread and node framing | `panes/chat/screen/chat_thread.py` | `panes/chat/showOnlyThis.ts` |
| Current state panel | `project/status/` | `panes/chat/statusPanel/` |
| Logs and a project's timeline | `project/timeline.py`, `api/activity_log.py` | `settings/logs/` |
| Archive (restore / delete) | `panes/create/lifecycle.py`, `storage/accounts_persistence.py` | `settings/archive/` |
| Every HTTP route | `api/requests_from_browser.py` | `api.ts` |

Backend paths are under `app/backend/`, UI paths under `app/ui/src/`.

## 3. Data on disk

Everything lives in `app/data/` as plain JSON:

| File | Holds |
|---|---|
| `projects/{id}/current.json` | The project now: name, account, `account_n`, and `plan.progression.steps` (the nodes) with `plan.node_id_hi` |
| `projects/{id}/events.jsonl` | One slim line per saved change: event, feedback, times, focus — the source for chat history, status, and logs |
| `accounts.json` | Accounts; a deleted one leaves a tombstone so its id is never reused |
| `saved_trees.json` | Saved trees per account, with `id_hi` |

- Ids that are never reused: node ids (per project), saved-tree ids,
  account ids, per-account project numbers. Global `project_id` is
  `max + 1`, so deleting the newest project frees its id.
- Every file is in the current format (converted once, 2026-09-27):
  there is no code for reading older formats. The `.bak` files in
  `data/` are leftovers from earlier conversions; nothing reads them.

## 4. The model

- Local **Ollama**, model `qwen3.5:9b`, temperature 0.2
  (`backend/model/client.py`). A reply with the wrong shape is not
  retried; the caller reports the failure.
- A Talk turn sends: fixed instructions (`model/brief/talk_prompt.py`:
  role, task, behavior, limits), the project's status, its last 10
  changes (`recent_changes_text()`), every label on the map, the
  selected node's path or every change on the selected day
  (`changes_on_day_text()`, up to 100), the last 20 turns, and the new
  message. The model is told to answer from the project only.
- The model sees labels only — not node ids, file contents, or anything
  outside the project.

## 5. Known limits

- No login; accounts are simulated. The server listens on localhost only.
- Add folder opens a macOS dialog on the server's machine.
- No written API reference (`TODO.md` Queue 30).
- `backend/foundation/` (time, math) is not used by anything.
- A node's `resolved` field is stored but nothing sets it; every node
  shows as open.
- Node ids are sequential per project (`p1`, `p2`, …), not globally
  unique (`TODO.md` Queue 50).
- Talk answers from the project's names and status only; it gives no
  general advice. It sees the last 10 changes, but their saved text is
  thin ("Imported 1 step(s)" does not say what) (`TODO.md` Active 46).

## 6. Open questions

- How much conversation the model should get — today the last 20 turns,
  all nodes mixed and tagged.
- What a "visit" is, if the app ever needs one (`TODO.md` Queue 27).

## See also

- `TODO.md` — what is being worked on
- [[03-architecture]] — how it is built
- [[05-decisions]] — why
