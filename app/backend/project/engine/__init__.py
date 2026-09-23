"""Project engine — Decide/Fill judgment and calendar, not a UI pane.

Layout:
  judgment/  decide, run_stage3, prompts, shape, ask
  time/      current_time (clock string for prompts), calendar (legacy steps)
  planner.py facade (still exposes generate_plan)
WHAT map lives in panes/canvas/.
"""
