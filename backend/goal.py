"""
Goal identity and grouping - which records belong to which goal, and
what a goal's current state is.

Split out of storage.py (2026-08-21) to match the product model in
docs/07-features.md ("Architecture framing: Program / Rooms /
Sitemap") - Goal is its own room. Built entirely on
storage.load_history() (the public read API), not storage's private
_load_all()/_save_all().

goal_id itself is still minted and backfilled inside storage.py (see
_next_goal_id()/_backfill_goal_ids()), not moved here: that happens at
save/load time, tightly coupled to the persistence mechanism itself -
splitting it out would mean storage.py importing back from this file
just to save a record, a real circular dependency rather than a clean
cut. What lives here is everything that only *reads* history and
groups it by goal_id, after the fact.
"""

from backend.storage import load_history


def get_history_for_goal(goal_id: int) -> list[dict]:
    """
    Return every record for one specific goal_id, oldest first - the
    goal's full back-and-forth: the original goal, then each
    feedback-and-replan round in order.

    A goal's history already *is* a conversation - each record's
    `feedback` is what the user said about the previous record's
    `right_now`, and its own `right_now` is the agent's reply - this
    just returns that chain so a template can render it as one instead
    of only ever showing the latest snapshot. See
    devtools/templates/_active_goal.html.
    """
    return [r for r in load_history() if r["goal_id"] == goal_id]


def get_latest_for_goal(goal_id: int) -> dict | None:
    """
    Return the most recent record for one specific goal_id, or None if
    no record has that goal_id.

    Needed once more than one goal can be active at a time (see
    docs/10-development.md, 2026-08-20): get_latest_plan() (storage.py)
    answers "what was touched most recently, across every goal", which
    stops being the right question the moment two goals are both active
    side by side on the board - giving feedback on one must never
    silently act on whichever goal happens to be globally newest.
    """
    for record in reversed(load_history()):
        if record["goal_id"] == goal_id:
            return record
    return None


def get_board() -> dict:
    """
    Group history into "active" and "completed" goals, for a board view
    (see docs/10-development.md, 2026-08-19).

    A "goal" isn't its own stored entity - it's a chain of records
    sharing the same `goal_id`, created by generate_plan() and then
    extended by replan() each time feedback comes in (see
    storage.save_plan()). So the only way to know a goal's current
    state is to find its most recent record. Records are loaded
    oldest-first, so iterating in order and overwriting by goal_id
    naturally leaves the latest record per goal.

    Grouping by goal_id (not `goal` text) is what makes this reliable:
    retyping a goal's text slightly differently ("take a shower" vs.
    "take shower") used to fragment it into separate board entries.
    goal_id is a stable identity assigned once and carried forward
    regardless of text - see docs/12-decisions.md, 2026-08-20.

    Returns {"active": [...], "completed": [...]}, each a list of
    records (latest state only, one per distinct goal).
    """
    latest_by_goal: dict[int, dict] = {}
    for record in load_history():
        latest_by_goal[record["goal_id"]] = record

    # .get(), not [] - records saved before the "completed" field
    # existed don't have the key at all.
    active = [r for r in latest_by_goal.values() if not r.get("completed")]
    completed = [r for r in latest_by_goal.values() if r.get("completed")]
    return {"active": active, "completed": completed}
