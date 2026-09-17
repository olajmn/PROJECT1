"""Turning a goal into a plan, and a plan into "what to do right now" -
decide.py (Stage 3 judgment: ASK/SUGGEST/PLAN),
generate_plan.py (orchestrates Decide then Fill + legacy steps +
shadow progression),
construct_progression.py (WHAT Step tree; shadow beside plan.steps),
planner.py (replan, steps, vision; re-exports generate_plan),
json_request.py (Plan-specific JSON-shape validation on top of the
shared model.client call), plan_prompts.py (system prompts),
plan_schema.py (PLAN_KEYS + shared prompt grounding),
plan_structure.py (week/session step fill)."""
