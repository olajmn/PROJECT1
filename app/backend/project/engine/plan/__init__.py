"""Turning a goal into a plan, and a plan into "what to do right now" -
decide.py (Stage 3 judgment: ASK/SUGGEST/PLAN),
generate_plan.py (orchestrates Decide then Fill + legacy steps +
shadow progression via project.panes.canvas.construct_first_map),
planner.py (replan, steps, vision; re-exports generate_plan),
json_request.py (Plan-specific JSON-shape validation on top of the
shared model.client call), plan_prompts.py (system prompts),
plan_schema.py (PLAN_KEYS + shared prompt grounding),
plan_structure.py (week/session step fill).

WHAT-tree writes live under project/panes/canvas/ (bead, construct_first_map,
edit_map, text_to_tree, call_suggest) — not in this folder.
"""
