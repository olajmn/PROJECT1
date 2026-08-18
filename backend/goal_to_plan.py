"""
MVP v0.2 - "Goal -> Structured Plan"

The user writes a goal, a local LLM (via Ollama) generates a plan as
STRUCTURED data (JSON) instead of free text, so the code can later pull
out exactly "what to do right now" instead of the whole plan.

Runs 100% locally - no API key, no internet, no cost.
Requires Ollama running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

Run from the PROJECT ROOT: .venv/bin/python -m backend.goal_to_plan
"""

import json

import ollama

from backend.storage import PLAN_KEYS, save_plan

MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "You are a personal execution agent. The user gives you a goal. "
    "Break the goal down into a concrete, realistic plan spanning multiple "
    "time horizons.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly these keys:\n"
    '  "one_year": string - where the user should be in about a year\n'
    '  "one_month": string - a concrete milestone for this month\n'
    '  "this_week": string - a concrete milestone for this week\n'
    '  "right_now": string - the SINGLE most immediate, concrete action '
    "the user can take this very moment. Small enough to start in the "
    "next 5 minutes.\n"
)

REPLAN_SYSTEM_PROMPT = (
    "You are a personal execution agent. The user already has a plan for "
    "their goal and is now giving you feedback on whether they completed "
    "the most immediate action ('right_now'). Adjust the plan based on "
    "this feedback:\n"
    "- If they did NOT complete it, make the next right_now action "
    "smaller and easier, or address the obstacle they mentioned.\n"
    "- If they DID complete it, move on to the next logical step.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly the "
    "same keys as before: one_year, one_month, this_week, right_now.\n"
)


def _ask_model(system_prompt: str, user_content: str) -> dict:
    """
    Shared call used by both generate_plan() and replan(): sends a system
    prompt + user message to the local model asking for JSON, parses the
    response, and validates it has the expected plan shape (PLAN_KEYS)
    before handing it back - so every caller can trust the shape instead
    of re-checking it themselves.
    """
    response = ollama.chat(
        model=MODEL,
        format="json",  # ask Ollama to constrain output to valid JSON
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    plan = json.loads(response["message"]["content"])

    missing = [key for key in PLAN_KEYS if key not in plan]
    if missing:
        raise ValueError(
            f"Model response is missing required plan key(s) {missing}: {plan}"
        )
    return plan


def generate_plan(goal: str) -> dict:
    """
    Takes a goal (a text string) and asks the local model to produce a
    structured plan. Returns a dict with keys: one_year, one_month,
    this_week, right_now.
    """
    return _ask_model(SYSTEM_PROMPT, f"My goal is: {goal}")


def replan(goal: str, previous_plan: dict, feedback: str) -> dict:
    """
    Takes the goal, the previous structured plan, and the user's feedback
    on the previous "right_now" action, and asks the model to produce an
    updated plan. Returns a dict with the same shape as generate_plan().
    """
    user_content = (
        f"My goal is: {goal}\n\n"
        f"The previous plan was: {json.dumps(previous_plan)}\n\n"
        f"My feedback on the 'right_now' action: {feedback}"
    )
    return _ask_model(REPLAN_SYSTEM_PROMPT, user_content)


# Only runs when this file is executed directly
# (not when other files import functions from it)
if __name__ == "__main__":
    my_goal = input("What do you want to achieve? ")
    print("\nThinking...\n")
    plan = generate_plan(my_goal)

    for horizon, text in plan.items():
        print(f"{horizon}: {text}")

    record = save_plan(my_goal, plan)
    print(f"\n[Saved as entry #{record['id']} in data/plans.json]")
