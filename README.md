# Personal AI Agent

- `current/` — the existing, verified prototype. Frozen as a working reference; not being restructured.
- `agent/` — the new application, built toward `docs/03-architecture.md` (named `v4/` until 2026-09-11 - see `docs/v4-migration-decision.md`; renamed since a version number baked into the directory name would need renaming again at every future milestone - versioning now happens as git tags instead, starting at `agent_4.0`).
- `docs/` — shared architectural/conceptual documentation (`03-architecture.md`, `v4-migration-decision.md`, `planning-model.md`) spanning both.

Each of `current/` and `agent/` is its own self-contained project (own `.venv/`, own `data/`, own `requirements.txt`) — see each one's own `README.md` to run it.
