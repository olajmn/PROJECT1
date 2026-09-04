"""
Plan Horizons

UI presentation data for Plan's time horizons - display labels, and
the ordered list shown alongside `now`. Presentation-only,
never read by Plan's own logic.
"""

from backend.goals.plan.planner import PLAN_KEYS

HORIZON_LABELS = {
    "year": "1 year",
    "month": "1 month",
    "week": "This week",
    "today": "Today",
    "hour": "This hour",
    "minute": "This minute",
}

# No "now" here - it gets its own highlighted box, read directly
# from record.plan.now, never through this label lookup.
BROADER_HORIZONS = [(key, HORIZON_LABELS[key]) for key in PLAN_KEYS if key != "now"]
