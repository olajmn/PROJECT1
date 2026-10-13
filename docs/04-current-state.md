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

`HOST` (default `localhost`) and `PORT` (default `8000`) can be set in the
environment; locally neither is needed.

### Demo mode

Set `DEMO_MODE=1` and `DEMO_PASSWORD` to put the public-demo checks in
front of every request (`backend/api/demo/`, [[05-decisions]] #70). Off by
default, and then nothing changes. On:

- One shared password; `POST /api/login` gives an in-memory session
  cookie, which ends on logout (sidebar, next to Settings), after
  30 minutes idle, or after 8 hours. A restart logs everyone out.
- Without a session, `/api/*` answers 401 and pages redirect to
  `ui/login.html`.
- Add folder and the folder chooser answer 403; bodies over 256 KB (chat
  8 KB) answer 413; Talk is limited per session, per IP, and per day
  (429); at most 50 sessions at once.
- Each login gets its own sandbox: a copy of `app/demo_seed/` (the
  account John Doe with "Project #1001" and "Getting in shape", copied
  from local data on 2026-10-14) in its own folder under `DEMO_SANDBOX_DIR`
  (default: the system temp directory), never `app/data/`. Storage reads
  and writes there for that session's requests
  (`backend/storage/sandboxes.py`); the folder is deleted when the
  session ends, and all are cleared at start.
- Trying it on `http://localhost` needs `DEMO_INSECURE_COOKIE=1`.

## 2. Where things are

The layers and their rules are in [[03-architecture]]. By feature:

| Feature | Backend | UI |
|---|---|---|
| Create, rename, archive, restore projects | `project/panes/create/` (`lifecycle.py`, `rename.py`) | `ui/src/panes/create/` |
| Accounts and which one owns a project | `storage/accounts_persistence.py`, `panes/create/project_account.py` | `panes/create/accounts/`, `settings/directory/` |
| What a node is; ids; sibling names | `project/node/` (see its `README.md`) | — |
| Add, remove, move, paste, folder | `panes/canvas/edit_map.py`, `text_to_tree.py`, `add_folder/` | `panes/canvas/` |
| Saved trees | `project/saved_trees/`, `storage/saved_trees_persistence.py` | `panes/canvas/savedTrees/` |
| The map as drawn | `api/answers_to_browser.py` (`map_tree()`) | `panes/canvas/drawNodes.ts`, `lines/`, `zoomAndPan/` |
| A Talk turn | `panes/chat/reply.py`, `model/brief/conversation.py`, `talk_prompt.py` | `panes/chat/` |
| Slash commands | `panes/chat/commands/` | `panes/chat/commands/` |
| The chat thread and its About frames (node or day) | `panes/chat/screen/chat_thread.py` | `panes/chat/showOnlyThis.ts`, `statusPanel/` |
| Current state panel | `project/status/` | `panes/chat/statusPanel/` |
| Logs and a project's timeline | `project/timeline.py`, `api/activity_log.py` | `settings/logs/` |
| Archive (restore / delete) | `panes/create/lifecycle.py`, `storage/accounts_persistence.py` | `settings/archive/` |
| Every HTTP route | `api/requests_from_browser.py` | `api.ts` |
| Demo mode: login, sessions, limits | `api/demo/` | `demo/`, `ui/login.html` |

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
  (`backend/model/client.py`), used for Talk replies only. A failed
  reply is not retried; the chat shows the error.
- `TALK_PROVIDER=openrouter` sends Talk to the same model hosted on
  OpenRouter (`qwen/qwen3.5-9b`, reasoning off, at most 400 output
  tokens; `backend/model/openrouter.py`), with the key from
  `OPENROUTER_API_KEY`. Meant for the public demo only ([[05-decisions]]
  #70); unset, Talk uses Ollama. An unknown value stops the server at
  start. `GET /api/model` shows the provider in use.
- A Talk turn sends: fixed instructions (`model/brief/talk_prompt.py`:
  role, task, behavior, limits), the project's status, its last 10
  changes (`recent_changes_text()`), every label on the map, the
  selected node's path or every change on the selected day
  (`changes_on_day_text()`, up to 100), the last 20 turns, and the new
  message. The model is told to answer from the project only.
- The model sees labels only — not node ids, file contents, or anything
  outside the project.

## 5. Known limits

- No login outside demo mode; accounts are simulated. The server listens
  on localhost unless `HOST` is set.
- Add folder opens a macOS dialog on the server's machine.
- No written API reference (`TODO.md` Queue 30).
- `backend/foundation/` (time, math) is not used by anything.
- A node's `resolved` field is stored but nothing sets it; every node
  shows as open.
- Node ids are sequential per project (`p1`, `p2`, …), not globally
  unique (`TODO.md` Queue 50).
- Talk answers from the project's names and status only; it gives no
  general advice. It sees the last 10 changes, but their saved text is
  thin ("Imported 95 nodes" counts every node but does not say which) (`TODO.md` Queue 38). What it must handle: [[02-product]] § 2.iii.

## 6. Open questions

- How much conversation the model should get — today the last 20 turns,
  all nodes mixed and tagged.
- What a "visit" is, if the app ever needs one (`TODO.md` Queue 27).

## See also

- `TODO.md` — what is being worked on
- [[03-architecture]] — how it is built
- [[05-decisions]] — why
