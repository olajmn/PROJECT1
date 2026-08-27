# Goal

**Status: CURRENT** - proven and working in the prototype.

What the user wants to achieve. A stable identity, independent of its
display text - a goal's text can be re-typed slightly differently without
fragmenting into a second goal, because identity is a minted id, not
text-matching.

## Owns

Identity and grouping: which records (see `plan/`) belong to the same
ongoing goal, and what that goal's current state is (its most recent
record - see `ARCHITECTURE.md`'s note on "state" not being a separate
store).

## Boundary

Does not own plan content, the immediate action, or feedback text - those
are `plan/`, `action/`, and `feedback/` respectively. A Goal without a Plan
yet is still a valid Goal (e.g. mid-clarification).

## Reference implementation

`backend/goals/goal/resolver.py` - `get_latest_for_all_goals()`, `get_latest_for_goal()`,
`get_history_for_goal()`. Identity fixed by a real, documented past bug: see
the prototype's `docs/05-decisions.md`, 2026-08-20, on why `goal_id` exists
instead of grouping by goal text.
