"""Project engine — reasoning (Decide/Fill) and calendar, not a UI pane.

Layout:
  judgment/  decide, run_stage3, prompts, shape, ask
  time/      current_time (clock string for prompts), calendar (legacy steps)
  reason.py  revise-from-feedback (replan / apply_new_duration)
WHAT map lives in panes/canvas/.
"""
