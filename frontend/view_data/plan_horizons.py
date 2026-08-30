"""
Plan Horizons

UI presentation data for Plan's time horizons - display labels, and
the ordered list shown alongside `right_now`. Presentation-only,
never read by Plan's own logic.
"""

from backend.goals.plan.planner import PLAN_KEYS

HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "today": "Today",
    "this_hour": "This hour",
    "this_minute": "This minute",
}

# No "right_now" here - it gets its own highlighted box, read directly
# from record.plan.right_now, never through this label lookup.
BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "right_now"]
