"""
Plan Horizons

UI presentation data for Plan's time horizons: display labels, and
which of them appear in the "broader plan" list templates render
alongside `right_now`. Never read by Plan's own logic - purely how
frontend words and orders things for display.
"""

from backend.goals.plan.planner import PLAN_KEYS

# A display label per PLAN_KEYS entry - not part of the Plan's shape
# (planner.PLAN_KEYS is that), just how each horizon is worded here.
# Presentation-only, never read by Plan's own logic. No "right_now"
# entry - BROADER_HORIZONS below excludes that key before ever looking
# it up here, and every template shows right_now directly from
# record.plan.right_now, never through this label lookup.
HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "today": "Today",
    "this_hour": "This hour",
    "this_minute": "This minute",
}

# The broader horizons shown alongside "right_now", on both the index
# page and the history page, in order, excluding "right_now" itself
# (which always gets its own highlighted box instead of being listed
# alongside the others). A goal with a short duration will have these
# come back as null/None - the templates skip any horizon that's falsy,
# so only the levels actually relevant to the goal show up.
BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]
