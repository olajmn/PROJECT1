# agent

The application, built toward `docs/03-architecture.md` (top-level `docs/`). See `docs/04-current-state.md` for what actually runs today.

Run with `-m` from within `agent/` (its own root) — use `.venv/bin/python`,
not system Python, since `ollama` (see `requirements.txt`) is only
installed there:

```
cd agent && .venv/bin/python -m server
```
