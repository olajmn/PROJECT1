# Public Demo Plan

The step plan for putting the existing app at a public URL as a demo; why it is limited this way: [[05-decisions]] #70 and its sandbox follow-up. Moves to `docs/archive/` when the demo is deployed.

## 1. Target

- A visitor opens the URL, enters the shared demo password, explores the seeded example projects, and can try everything the app does, Talk included.
- Each visitor works in their own sandbox: a fresh copy of the demo data for their session. Nothing they do is seen by anyone else or outlasts their session.
- Local use is unchanged: without demo mode, there is no login, no sandbox, every route works on `app/data/`, and Talk uses local Ollama.
- About one working day plus the sandbox work, with a checkpoint (§ 4). A real blocker is written down and the deploy waits; an unsafe deploy is not the fallback.

## 2. Scope

**In:** shared demo login and sessions, a sandbox per session, two blocked routes, request and Talk limits, a Talk provider switch, seeded demo data, one Docker image on one host with HTTPS, a public smoke test, and docs.

**Out:** individual users, registration, a database, file locking, keeping a visitor's work after their session, hiding the blocked folder actions in the UI, a model change for quality, and the #69 work ([[auth-plan]], paused).

## 3. Design

### i. Demo mode

- Off unless `DEMO_MODE` is set. Everything below applies only in demo mode.
- New code in its own folder (e.g. `app/backend/api/demo/`), called from `Handler` in `backend/api/requests_from_browser.py` with a thin check (`CONVENTIONS.md` § New code placement).

### ii. Login and sessions

- One password, `DEMO_PASSWORD`, from a hosting secret, compared with `hmac.compare_digest`. No users file.
- `POST /api/login` creates a session: a random token (`secrets`) in memory with `created` and `last_seen`, and creates its sandbox (§ 3.iv). Cookie: `HttpOnly; Secure; SameSite=Strict; Path=/`.
- A session ends on `POST /api/logout`, after 30 minutes without a request, or 8 hours after login, whichever comes first. Both limits are read from the environment, so the smoke test can shorten them. Ending a session deletes its sandbox.
- Sessions live in memory; a restart logs everyone out.
- Login attempts are rate-limited per client IP.
- Without a session: `/api/*` (except login) answers 401; a page request is redirected to a static `app/ui/login.html`. Every `fetch` lives in `app/ui/src/api.ts`; one wrapper set up at startup sends the browser to the login page on any 401.

### iii. Route protection

- Every route works inside a sandbox, including rename, archive, restore, permanent delete, and accounts: they only change that visitor's copy.
- Blocked (403), because they reach the server itself rather than the sandbox: `map/folder` (its `folder_tree()` in `add_folder/walk.py` resolves any server path the client sends and lists the names it finds) and `choose-folder` (runs `osascript`).
- `_read_json_body()` refuses bodies over a fixed size; chat text has a maximum length.
- Talk: a per-session and per-IP rate limit and a daily cap on model calls, plus the per-key credit limit at OpenRouter.
- Static files are already confined to `app/ui/` (`_find_file()` in `files_to_browser.py`).

### iv. Sandboxes

- Seed data lives in the repository, in a folder not named `data/` (`.gitignore` ignores `data/` at any depth), e.g. `app/demo_seed/`. It holds demo projects only and is never written to.
- A new session copies the seed into its own folder under a sandbox root (`SANDBOX_DIR`, default a folder in the system temp directory, never inside `app/data/`).
- Storage reads and writes under the current request's folder. Today the location is fixed when the storage modules load: `DATA_DIR` in `backend/storage/paths.py`, and the paths built from it in `project_persistence.py` (`PROJECTS_DIR`), `accounts_persistence.py` (`ACCOUNTS_FILE`), and `saved_trees_persistence.py` (`SAVED_TREES_FILE`). These become lookups of the current folder, set by `Handler` for each request in demo mode (a context variable). Without demo mode the current folder is `app/data/`, so local use is unchanged. Nothing in storage caches data between requests.
- Expired sandboxes are deleted when their session ends and in a sweep on each request; on start, the sandbox root is emptied (no session survives a restart).
- A cap on sandboxes at once (and so on disk use); a login over the cap is refused with a clear message.
- Sandboxes do not need to survive a restart, so the host needs no persistent volume.
- Personal data never reaches the host: `.dockerignore` excludes `app/data/`, because the deploy tool uploads the local folder, not Git.

### v. Talk

- `send_chat()` in `backend/model/client.py` stays the one boundary; prompt building, history, saving the reply, and the 503 on failure (`_model_failed()`) stay as they are.
- A provider switch inside it: `ollama` (default, unchanged) or OpenRouter, chosen by `TALK_PROVIDER=openrouter`; key from `OPENROUTER_API_KEY` (a hosting secret); reasoning off, 400 output tokens at most, 60-second timeout (`backend/model/openrouter.py`). `GET /api/model` reports the provider in use. Built (step 3).
- The switch does not limit use by itself: the login and Talk limits in § 3.ii–iii and the per-key credit limit at OpenRouter do.

### vi. Hosting

- One Docker image: a Node stage builds `app/ui` with `tsc`; a Python stage runs `python -m server` with `HOST`/`PORT` from the environment (today `"localhost"` in `server.py` and `PORT = 8000` in `requests_from_browser.py`). The seed is part of the image.
- One host instance with HTTPS at its edge; no volume (§ 3.iv). Planned host: Fly.io; confirmed at step 7 against current pricing.

## 4. Steps

| # | Step | Estimate |
|---|---|---|
| 1 | Talk test outside the repository (§ 5). Done | — |
| 2 | `HOST` / `PORT` from the environment | 15 min |
| 3 | Provider switch in `send_chat()`; local Ollama still default. Built | — |
| 4 | Demo mode: login and sessions, 401 handling, the two blocked routes, size limits, Talk limits | 2–2.5 h |
| 5 | Sandboxes: storage paths per request, create on login, delete on session end, sweep and cap; tests that two sessions cannot see each other's changes and that local mode still uses `app/data/` | 2–4 h |
| **Checkpoint** | Steps 2–5 work locally with `DEMO_MODE` set: two browsers logged in at once each see only their own changes, and local mode is unchanged. If not, stop and reassess; an unsafe deploy is not the fallback. | |
| 6 | Seed data: 2–3 demo projects | 1–2 h, mostly content |
| 7 | `Dockerfile`, `.dockerignore`; host setup: account, secrets, deploy | 2 h |
| 8 | Public smoke test (§ 7) and docs (`04-current-state.md`, this plan to `archive/`) | 45 min |

Critical path: 4 → 5 → 7 → 8. Steps 2 and 6 can run beside it.

## 5. Talk test

Before any code depends on a provider, compare candidates on the same input:

- **Input:** 3–5 real Talk requests captured from local projects (the `messages` list `build_messages()` produces), sent unchanged.
- **Baseline:** the same requests against local Ollama, `qwen3.5:9b`.
- **Measured per candidate:** availability of the same model; whether reasoning can be turned off; latency per reply; tokens used and the resulting cost; answer quality against the baseline; free-tier and rate limits; whether a hard spending cap exists.
- A free model or tier counts only if it passes the same checks; it is not assumed sufficient.
- The test script and API keys stay outside the repository.
- **Result (2026-10-13):** OpenRouter `qwen/qwen3.5-9b` with `reasoning: {"enabled": false}`: all 10 calls (5 cases, twice) HTTP 200, 0 reasoning tokens, about 1.2–2.3 s each, about $0.00095 in total, routed to SiliconFlow. Replies matched local Ollama closely, including its mistake on the selected-day case (parts added on 11 Oct named as added on 12 Oct). Chosen for the demo.

## 6. Open questions

- The client IP header behind the host's proxy, for per-IP limits.
- The cap on sandboxes at once, and the Talk limits (per session, per IP, per day).
- Whether to require zero data retention at OpenRouter (the test calls went to SiliconFlow).
- The first image build happens on the host's remote builder: Docker is not installed locally.

## 7. Smoke test

Against the public URL:

- HTTPS; `/` without a session goes to the login page; `/api/projects` without a session is 401.
- A wrong password fails; repeated attempts are limited.
- Logout ends the session; the old cookie then gets 401.
- With shortened limits: the inactivity timeout and the maximum lifetime both end a session.
- Two browsers logged in at once: a rename, archive, delete, or chat in one is not visible in the other; a new login starts from the seed again.
- Map: add, remove, move, paste, save and insert a tree.
- Talk replies in acceptable time; an over-long message is refused; the rate limit answers clearly.
- `map/folder` with `{"path": "/"}` and `choose-folder` answer 403.
- An over-size body is refused.
- After a session ends, its sandbox folder is gone.
- Locally, without `DEMO_MODE`, the app behaves as before on `app/data/` and Talk uses Ollama.
