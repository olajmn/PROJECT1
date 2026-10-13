# Demo

How the public demo works, where its code lives, and how to run and update it.

## 1. What it is

The app at https://ojmn.fly.dev behind one shared password. Each login gets its own copy of the demo data, deleted when the session ends. Without `DEMO_MODE` none of this runs and the app works as always.

## 2. Where the code is

| Part | File |
|---|---|
| Login, sessions, blocked routes, limits | `app/backend/api/demo/` (`check.py`, `settings.py`) |
| One data folder per visitor | `app/backend/storage/sandboxes.py` |
| Talk via OpenRouter | `app/backend/model/openrouter.py`, switch in `client.py` |
| Login page, Log out | `app/ui/login.html`, `app/ui/src/demo/` |
| What every visitor starts with | `app/demo_seed/` |
| Hosting | `app/Dockerfile`, `app/.dockerignore`, `app/fly.toml` |

## 3. Settings

| Variable | Set in | Meaning |
|---|---|---|
| `DEMO_MODE` | `fly.toml` | `1` turns the demo on |
| `DEMO_PASSWORD` | Fly secret | the shared password |
| `TALK_PROVIDER` | `fly.toml` | `openrouter`; unset means Ollama |
| `OPENROUTER_API_KEY` | Fly secret | key with its own credit limit |
| `DEMO_IDLE_SECONDS`, `DEMO_MAX_SECONDS` | optional | default 30 min and 8 h |

Other limits (sessions at once, Talk per minute and per day, body sizes) are in `settings.py`.

## 4. Run and update

- Locally, from `app/`: `DEMO_MODE=1 DEMO_PASSWORD=test DEMO_INSECURE_COOKIE=1 .venv/bin/python -m server`
- Publish a change: commit, then `fly deploy` from `app/`. A deploy restarts the server and logs everyone out.
- New password: change the `DEMO_PASSWORD` secret on Fly.io, then deploy.
- New demo content: replace `app/demo_seed/` with a copy of the projects to show, then deploy.
- Stop it (no cost): `fly scale count 0`; start again with `fly scale count 1`.

## See also

- [[05-decisions]] #70 — why it is built this way
- `public-demo-plan.md` in the archive — how it was built and tested
