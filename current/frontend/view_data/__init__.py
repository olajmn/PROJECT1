"""Prepares already-decided backend information for `templates/` to
render - grouping/splitting goal history for the overview pages
(goal_overview.py), joining/splitting plan and message text for
display (text_formatting.py), and Plan's time-horizon display labels
(plan_horizons.py). No Flask dependency, no Goal/Plan/Vision/Feedback
decisions - view preparation, not the views themselves (`templates/`)
and not a domain capability (`backend/`).

Split out of frontend/ directly into its own package 2026-08-30, once
it was clear these three modules share one responsibility (shaping
backend output for templates) distinct from both `app.py` (routing)
and `templates/` (the actual HTML/Jinja)."""
