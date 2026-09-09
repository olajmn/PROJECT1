# Action

**Status: CURRENT** - proven and working in the prototype (as part of
Plan's data - see below).

What the user does right now. The narrowest, most immediate slice of Plan -
not a separate strategy, just the current pointer into one.

## Not to be confused with Execution

"Action" here means the user's own next step. It does **not** mean the
agent performing something in the real world (creating a file, calling an
API) - that's `../../execution/`, a distinct, unbuilt component. Keeping
these as two different words is deliberate - see `ARCHITECTURE.md`'s
"Two different meanings of Action."

## Boundary

Modeled as its own component here even though the prototype currently
implements it as a field inside Plan's own object (`plan.right_now`), not a
separate structure - see `../plan/README.md` for why that's flagged, not
resolved, in this skeleton.

## Reference implementation

`plan["right_now"]` and `plan["steps"]` in `backend/goals/plan/planner.py`;
advanced via `frontend/app.py`'s `/step` route (pure index arithmetic, no
model call - the step list was already decided upfront). The prototype's UI
labels this row "Action (right now)" - the same terminology consolidation
this skeleton uses throughout.
