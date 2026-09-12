# Personal AI Agent

- `agent/` — the application, built toward `docs/03-architecture.md` (named `v4/` until 2026-09-11 - see `docs/v4-migration-decision.md`; renamed since a version number baked into the directory name would need renaming again at every future milestone - versioning now happens as git tags instead, starting at `agent_4.0`).
- `docs/` — architectural/conceptual documentation (`03-architecture.md`, `v4-migration-decision.md`, `planning-model.md`).

`current/` — the prototype `agent/`'s Planning capability was originally copied from — no longer exists in this repository. It was deleted as an unintentional side effect of the same 2026-09-11 commit that renamed `v4/` to `agent/` (see `docs/04-current-state.md` § 6 for how this was found and confirmed, 2026-09-12); nothing that actually ran was lost, since the proven code and a frozen frontend reference were both copied into `agent/` beforehand, but `current/` itself can no longer be opened directly to check anything against it.

See `agent/`'s own `README.md` to run it.
