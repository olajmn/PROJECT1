# Public Demo Plan

The step plan for putting the existing app at a public URL as a demo; why it is limited this way: [[05-decisions]] #70. Moves to `docs/archive/` when the demo is deployed.

## 1. Target

- A visitor opens the URL, enters the shared demo password, explores a seeded example project, edits the map, and tries Talk.
- Each visitor has their own session; all visitors share one demo dataset.
- Local use is unchanged: without demo mode, there is no login, every route works, and Talk uses local Ollama.
- One working day, with a checkpoint after about four hours (§ 4). A real blocker is written down and the deploy waits; an unsafe deploy is not the fallback.

## 2. Scope

**In:** shared demo login and sessions, a route allowlist, request and Talk limits, a Talk provider switch, seeded demo data and a manual reset, one Docker image on one host with a persistent volume and HTTPS, a public smoke test, and docs.

**Out:** individual users, registration, per-visitor data, a database, file locking, a scheduled reset, hiding blocked actions in the UI, a model change for quality, and the #69 work ([[auth-plan]], paused).

## 3. Design

### i. Demo mode

- Off unless `DEMO_MODE` is set. Everything below applies only in demo mode.
- New code in its own folder (e.g. `app/backend/api/demo/`), called from `Handler` in `backend/api/requests_from_browser.py` with a thin check (`CONVENTIONS.md` § New code placement).

### ii. Login and sessions

- One password, `DEMO_PASSWORD`, from a hosting secret, compared with `hmac.compare_digest`. No users file.
- `POST /api/login` creates a session: a random token (`secrets`) in memory with `created` and `last_seen`. Cookie: `HttpOnly; Secure; SameSite=Strict; Path=/`.
- A session ends on `POST /api/logout`, after 30 minutes without a request, or 8 hours after login, whichever comes first. Both limits are read from the environment, so the smoke test can shorten them.
- Sessions are never written to `data/`; a restart logs everyone out.
- Login attempts are rate-limited per client IP.
- Without a session: `/api/*` (except login) answers 401; a page request is redirected to a static `app/ui/login.html`. Every `fetch` lives in `app/ui/src/api.ts`; one wrapper set up at startup sends the browser to the login page on any 401.

### iii. Route protection

- POST routes run only if on an allowlist; everything else answers 403. Allowed: map edits (`map`, `remove`, `move-up/down`, `import`, `save-tree`, `insert-tree`), `parse-outline-preview`, `chat`. Whether project create / rename / cancel / restore are allowed is open (§ 6).
- Blocked: `map/folder` (its `folder_tree()` in `add_folder/walk.py` resolves any server path the client sends and lists the names it finds), `choose-folder` (runs `osascript`), every `/api/accounts…` route, project `delete` and `user`, and saved-tree `delete`.
- `_read_json_body()` refuses bodies over a fixed size; chat text has a maximum length.
- Talk: a per-IP rate limit and a daily cap on model calls, plus a hard spending cap at the provider.
- Static files are already confined to `app/ui/` (`_find_file()` in `files_to_browser.py`).

### iv. Data and reset

- Seed data lives in the repository, in a folder not named `data/` (`.gitignore` ignores `data/` at any depth), e.g. `app/demo_seed/`. It holds demo projects only.
- On start, an empty `/app/data` is filled from the seed. A reset command copies the seed over `data/` and is run by hand on the host; it does not touch sessions.
- Storage is unchanged: JSON/JSONL on one instance, on a persistent volume mounted at `app/data` (where `DATA_DIR` in `backend/storage/paths.py` already points).
- Personal data never reaches the host: `.dockerignore` excludes `app/data/`, because the deploy tool uploads the local folder, not Git.

### v. Talk

- `send_chat()` in `backend/model/client.py` stays the one boundary; prompt building, history, saving the reply, and the 503 on failure (`_model_failed()`) stay as they are.
- A provider switch inside it: `ollama` (default, unchanged) or an OpenAI-compatible API, configured by base URL, model, API key (secret), a timeout, and reasoning off. `GET /api/model` reports the provider in use.
- Which provider is decided by the test in § 4 step 1, not before.

### vi. Hosting

- One Docker image: a Node stage builds `app/ui` with `tsc`; a Python stage runs `python -m server` with `HOST`/`PORT` from the environment (today `"localhost"` in `server.py` and `PORT = 8000` in `requests_from_browser.py`).
- One host instance with a persistent volume and HTTPS at its edge. Planned host: Fly.io; confirmed at step 7 against current pricing.

## 4. Steps

| # | Step | Estimate |
|---|---|---|
| 1 | Talk test outside the repository (§ 5) | 1–1.5 h |
| 2 | `HOST` / `PORT` from the environment | 15 min |
| 3 | Provider switch in `send_chat()`; local Ollama still default | 1–1.5 h |
| 4 | Demo mode: login and sessions, 401 handling, allowlist, size limits, Talk limits | 2–2.5 h |
| **Checkpoint (~4 h)** | Steps 1–4 work locally with `DEMO_MODE` set. If not, stop and reassess: shipping with Talk blocked is an option, an unsafe deploy is not. | |
| 5 | Seed data (2–3 demo projects) and the reset command | 1–2 h |
| 6 | `Dockerfile`, `.dockerignore`, start step that seeds an empty volume | 1 h |
| 7 | Host setup: account, volume, secrets, deploy | 1 h |
| 8 | Public smoke test (§ 7) and docs (`04-current-state.md`, this plan to `archive/`) | 45 min |

Critical path: 1 → 3 → 4 → 6 → 7 → 8. Steps 2 and 5 can run beside it.

## 5. Talk test

Before any code depends on a provider, compare candidates on the same input:

- **Input:** 3–5 real Talk requests captured from local projects (the `messages` list `build_messages()` produces), sent unchanged.
- **Baseline:** the same requests against local Ollama, `qwen3.5:9b`.
- **Measured per candidate:** availability of the same model; whether reasoning can be turned off; latency per reply; tokens used and the resulting cost; answer quality against the baseline; free-tier and rate limits; whether a hard spending cap exists.
- A free model or tier counts only if it passes the same checks; it is not assumed sufficient.
- The test script and API keys stay outside the repository.

## 6. Open questions

- Whether visitors may create, rename, archive, and restore projects, or only edit the map and use Talk.
- Which Talk provider (after § 5).
- The client IP header behind the host's proxy, for per-IP limits.
- The first image build happens on the host's remote builder: Docker is not installed locally.

## 7. Smoke test

Against the public URL:

- HTTPS; `/` without a session goes to the login page; `/api/projects` without a session is 401.
- A wrong password fails; repeated attempts are limited.
- Logout ends the session; the old cookie then gets 401.
- With shortened limits: the inactivity timeout and the maximum lifetime both end a session.
- Map: add, remove, move, paste, save and insert a tree.
- Talk replies in acceptable time; an over-long message is refused; the rate limit answers clearly.
- Blocked routes answer 403, including `map/folder` with `{"path": "/"}`, `choose-folder`, `accounts`, and project `delete`.
- An over-size body is refused.
- After a reset the seed data is back and logged-in visitors stay logged in.
- The host's `app/data` holds only seed data.
- Locally, without `DEMO_MODE`, the app behaves as before and Talk uses Ollama.
