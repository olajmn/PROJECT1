"""Project engine — Decide/Fill judgment and WHEN calendar, not a UI pane.

Layout (2026-09-20):
  judgment/  decide, run_stage3, prompts, shape, current_time, ask
  when/      calendar (legacy steps)
  planner.py facade (still exposes generate_plan)
WHAT map lives in panes/canvas/.
"""
