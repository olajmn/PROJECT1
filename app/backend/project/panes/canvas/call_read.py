"""
Read an existing WHAT tree back into words, on demand: one summary of
what the project appears to be about, plus a one-line seed - the goal
sentence the tree would have grown from.

This inverts the usual direction. create_goal() reads a sentence and
asks the planner to produce a tree; here the tree already exists (built
by hand, or pasted through text_to_tree.py) and the sentence is derived
from it. Nothing in persistence depends on the old order, so the two
directions are equally valid ways in - see create_empty_project().

Nothing here writes, same rule as call_suggest.py: this module asks and
returns. Whether a reading is kept, and whether its seed replaces the
project's own text, is a decision for the caller and is deliberately
not made here.

ONE call, not two. The summary and the seed are two phrasings of the
same judgement - what is this tree about - so splitting them would ask
the model the same question twice and invite the two answers to
disagree. That is the opposite situation from call_suggest.py's
verdict-then-decompose split, where the two calls genuinely do
different jobs.
"""

# Contents
#  1. Reading
#      - read_tree()
#
#  2. Rendering the tree for the model
#      - outline_of()

import json

from backend.llm_client import send_message

READING_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "seed": {"type": "string"},
    },
    "required": ["summary", "seed"],
}

SYSTEM_PROMPT = (
    "You are given the structure of a project someone has already "
    "built or pasted in - a tree of labels, indented to show what "
    "sits under what. Nobody has written down what the project is "
    "about; that is what you work out from the structure alone.\n\n"
    "Return two things.\n\n"
    "`summary`: a few sentences on what this project appears to be "
    "about - what it covers, how it is organised, and what kind of "
    "work it implies. Describe what is actually there. Do not "
    "recommend, judge whether it is good, or propose what is "
    "missing.\n\n"
    "`seed`: one sentence, the goal this tree would have grown from, "
    "written the way the person would have written it themselves "
    "before building any of it. Short and plain - not a restatement "
    "of the summary."
)

# A tree far past this is cheaper to truncate than to fail on, and the
# shape is legible from the first levels anyway. A ceiling, not a target.
MAX_LINES = 400


def read_tree(goal_label: str, steps: list[dict]) -> dict | None:
    """
    {"summary", "seed"} for this tree, or None if there is nothing to
    read. `goal_label` is the project's current display text, given as
    context only - the model is told to work from the structure, and
    an untitled or throwaway name should not steer it.
    """
    outline = outline_of(steps)
    if not outline:
        return None

    raw = send_message(
        SYSTEM_PROMPT,
        f"Project is currently called: {goal_label}\n\nIts structure:\n{outline}",
        schema=READING_SCHEMA,
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    summary = (parsed.get("summary") or "").strip()
    seed = (parsed.get("seed") or "").strip()
    if not summary or not seed:
        return None
    return {"summary": summary, "seed": seed}


def outline_of(steps: list[dict], depth: int = 0) -> str:
    """The tree as indented lines - the same shape text_to_tree.py
    parses, so what the model reads is what a person would paste."""
    lines: list[str] = []
    _collect(steps, depth, lines)
    return "\n".join(lines[:MAX_LINES])


def _collect(steps: list[dict], depth: int, lines: list[str]) -> None:
    for step in steps:
        if not isinstance(step, dict):
            continue
        label = (step.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
        children = step.get("children")
        if isinstance(children, list):
            _collect(children, depth + 1, lines)
