"""
Global conversation entry (Conversation tab / `/api/message`).

Same *path level* under `backend/` as `planning/`, but not the same
*kind* of thing:

- `planning/chat/` - Active per-goal chat (goal id already known)
- `global_conversation/` - free-chat orchestrator: Describe → Decide
  (intake) → Planning or Voice alone. Does not own goal/vision state.

Sibling folders, different jobs. Live wiring still lives in
`cli.py`'s `process_turn()` until moved here (into `turn.py`); this
package exists so the place for that entry is named clearly.
"""
