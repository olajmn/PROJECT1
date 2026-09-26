# Infrastructure

**Status: CURRENT** - proven and working in the prototype.

Shared technical machinery used by the system that does not itself
represent something the agent understands. Persistence is the clear
example: it stores and retrieves data without interpreting what that data
means - see `../foundation/README.md` for the fuller Domain/Faculty/
Infrastructure distinction this follows.

## Owns

Reading and writing the agent's data, atomically, in a portable, human-
readable format. Used by every component that stores or moves data - not
owned by any single one of them.

## Boundary

Infrastructure never decides anything and never interprets meaning - a
component that starts making judgment calls about the data it holds isn't
Infrastructure anymore, it's a Faculty or Domain capability that happens to
also touch storage.

## Reference implementation

`backend/store/` — local JSON, atomic (`project_persistence.py`, `users_persistence.py`, `paths.py`)
temp-file-then-rename writes, no database. See the prototype's
`docs/05-decisions.md` #14 for why SQL/a database isn't justified at this
project's actual scale.
