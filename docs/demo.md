# Demo

How the public demo works, where its code lives, and how to run and update it.

## 1. What it is

The app at https://demo-one.fly.dev behind one shared password. Each login gets its own copy of the demo data, deleted when the session ends. Without `DEMO_MODE` none of this runs and the app works as always.

## 2. Where the code is

| Part | File |
|---|---|
| Login, sessions, blocked routes, limits | `app/backend/api/demo/` (`check.py`, `settings.py`) |
| One data folder per visitor | `app/backend/storage/sandboxes.py` |
| The chat via OpenRouter | `app/backend/model/openrouter.py`, switch in `client.py` |
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
| `DEMO_START_PROJECT_ID` | `fly.toml` | the project every login opens (`56`, Project #1001) |
| `DEMO_MAP_START_DEPTH` | optional | levels a map opens with after login; default 3 |

Other limits (wrong passwords per IP, sessions at once, chat messages per minute and per day, body sizes) are in `settings.py`.

## 4. Services and costs

| Service | What it does | Where it is managed | Cost and limits |
|---|---|---|---|
| Fly.io | Runs the app: app `demo-one`, one always-on machine (256 MB) in `arn` | fly.io dashboard → `demo-one` (Secrets, Usage, Billing) | About $2.19 a month for the machine plus a little outbound traffic (Fly.io price list, checked 2026-10-13). No spending cap exists on Fly.io; check Usage |
| OpenRouter | Answers the chat with `qwen/qwen3.5-9b` | openrouter.ai → Keys: key `demo-one` | About $0.0001 per chat message (test of 2026-10-13). The key has a $1 total limit; when it is used up, the chat stops answering and the rest works. Raise the limit on that page |

The demo also caps the chat at 500 messages a day (`settings.py`). Chat messages pass through OpenRouter and the provider it picks (SiliconFlow in the tests); `TODO.md` 61 is whether to require zero data retention.

## 5. Run and update

- Locally, from `app/`: `DEMO_MODE=1 DEMO_PASSWORD=test DEMO_INSECURE_COOKIE=1 .venv/bin/python -m server`
- Publish a change: commit, then `fly deploy` from `app/`. A deploy restarts the server and logs everyone out.
- New password: change the `DEMO_PASSWORD` secret on Fly.io, then deploy.
- New demo content: replace `app/demo_seed/` with a copy of the projects to show, then deploy.
- Stop it (no cost): `fly scale count 0`; start again with `fly scale count 1`.

## See also

- [[05-decisions]] #70 — why it is built this way
- How it was built and tested: the step plan `public-demo-plan.md`, in git history (removed 2026-10-14)
