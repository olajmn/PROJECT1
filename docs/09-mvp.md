# 09 — MVP

> Phase 7 in [[00-project-brief]]. See [[06-user-flows]] for the full flow.

**This is "Prototype 0.1"** — the smallest version of the full agent
loop in [[04-hypothesis]] that closes the circle (goal → plan → action →
feedback → replan → next action). Not a one-time plan generator.

## Target flow for the MVP

```
User writes a goal
↓
LLM creates a plan
↓
Plan is saved
↓
User gets today's task
↓
User reports progress
↓
LLM can adjust the plan
```

## Status

| Step | Status | File |
|---|---|---|
| Goal → Plan | ✅ Working | `backend/agent/specialized/plan.py` (structured JSON: one_year/one_month/this_week/today/this_hour/this_minute/right_now) |
| Plan is saved | ✅ Working | `backend/storage.py` (JSON history, `data/plans.json`) |
| Today's task | ✅ Working | `backend/agent/specialized/today.py` — shows just `right_now` from the latest plan |
| User reports progress | ✅ Working | `devtools/app.py` `/feedback` route (web form) |
| LLM adjusts the plan | ✅ Working | `backend/agent/specialized/plan.py` `replan()` |

**Prototype 0.1's loop is closed end-to-end** (2026-08-18): goal → plan →
right now → user feedback → replan → new right now, tested via
`devtools/app.py` (run: `.venv/bin/python -m devtools.app`
from the project root). Next: real usage/testing (see Testing philosophy
below), not more features.

**Important distinction:** "✅ Working" above means the *mechanism*
works — the code correctly calls the LLM, saves, and displays the
result. It does **not** mean the agent's answers are always accurate.
The model has already been caught hallucinating a specific, unfounded
detail (see [[11-experiments]]) — the plumbing works, the water isn't
guaranteed clean. Don't conflate the two when reporting progress.

## Testing philosophy

First user is the project owner, testing on themselves. Explicitly
**not needed** to test the core hypothesis: web app, mobile app, voice,
cloud, advanced UI, an aggregator system, or an advanced memory database.
The question that matters right now:

> Can the agent actually help me do something I would otherwise have
> struggled to do?

If Prototype 0.1 works well → build further. If it doesn't → find out
why before building more. Testing takes priority over further
ideation — see [[12-decisions]].

## See also

- [[08-technical-architecture]]
- [[10-development]]
