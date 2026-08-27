"""Turning a goal into a plan, and a plan into "what to do right now" -
planner.py (goal -> structured plan via the LLM, plus replan()),
model_client.py (generic LLM call + shape validation), step_generator.py
(the narrower model call that fills in a plan's step list), and
action_reader.py (read-only: just the current Action/`right_now` from
the latest saved plan).

Split into these four modules 2026-08-27 (previously one file,
plan.py)."""
