"""Turning a goal into a plan, and a plan into "what to do right now" -
plan.py (goal -> structured plan via the LLM, plus replan()) and
today.py (just today's immediate action from the latest saved plan).
Not yet split into data/logic like goal/ or time/ - plan.py currently
mixes both (PLAN_KEYS/HORIZON_LABELS/prompts alongside generate_plan()/
replan()), unresolved as of 2026-08-25."""
