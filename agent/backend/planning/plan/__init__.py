"""Turning a goal into a plan, and a plan into "what to do right now" -
planner.py (goal -> structured plan via the LLM, plus replan()),
model_client.py (Plan-specific JSON-shape validation on top of the
shared reasoning.model_client call), plan_prompts.py (the two system
prompts planner.py's ask_model() calls send), plan_structure.py (the
model call that decides a plan's step count and content, each step
optionally carrying its own microsteps)."""
