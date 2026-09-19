"""
One level of decomposition, on demand: given a step and the path it
sits under, raise the resolution of that one point in the plan -
never a whole sub-tree. This is docs/planning-model.md §
Decomposition / zoom; that section deliberately does NOT decide
whether the finer content is persisted, so nothing here writes
anything.

Asking for one flat level is easier for the local model than asking
for a nested one, not harder: CHILDREN_SCHEMA has no recursion in it,
and Ollama constrains generation to the schema rather than only to
valid JSON syntax the way format="json" does. Depth grows by calling
zoom_into() again on a child, so no single response ever carries a
tree.

`duration` is required for the same reason generate_structure()
returns None without a resolvable span: there is nothing honest to
break a step into without the timeframe it has to fit inside. A goal
is not plannable from its wording alone in this project - see
create_goal()'s clarification/suggested_duration branches.

TWO calls, deliberately - the depth verdict is asked separately from
the decomposition, and measured to need to be. Asked to judge and
decompose at once, the model always took the cheap branch: given a
schema where "no children" was valid, it returned empty for all five
test steps including "climb Mount Everest" over 18 months. Asked to
do nothing but judge (is_too_coarse()), it was unanimous and correct
on five of seven cases, and when forbidden to stop it decomposed
well. It can do either job; it collapses when one call has to do
both. Note this is the opposite finding from calendar.py's
one-call rule, and not a contradiction of it: what destabilized that
module was a second call CONSUMING the first's output, where here the
verdict only gates whether the second call happens.

Known weak spot: the verdict is least reliable at the bottom, where
it matters least in practice - "open the document and write the first
paragraph" (§ Structural axis's own example of an Action) was called
too coarse twice in three. A step is never force-expanded, so the
cost of that miss is an offered zoom that should not have been
offered, not a wrong tree.
"""

import json

from backend.llm_client import send_message

COARSENESS_SCHEMA = {
    "type": "object",
    "properties": {"too_coarse": {"type": "boolean"}},
    "required": ["too_coarse"],
}

CHILDREN_SCHEMA = {
    "type": "object",
    "properties": {
        "children": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}},
                "required": ["label"],
            },
        },
    },
    "required": ["children"],
}

# § Adaptive depth's own question, kept as literally as it is written
# there. The wording is load-bearing, not decoration: an earlier
# version asked whether a step was "concrete enough to just do",
# which the model could not judge in either direction - it called
# "climb Mount Everest" finished two times in three, and once that
# was tightened it broke "drink a glass of water" into six steps.
COARSENESS_SYSTEM_PROMPT = (
    "You judge ONE thing about a step in a plan: is it still too "
    "coarse to be a meaningful next unit of work, or is it already at "
    "a resolution where a concrete next action could be projected "
    "from it directly?\n\n"
    "Set too_coarse to true if the step still needs breaking down "
    "before anyone could act on it. Set it to false if a person could "
    "already project a concrete next action straight from it.\n\n"
    "Judge the step at the position it actually sits in - a step deep "
    "under several larger ones is usually nearer to being actionable "
    "than the goal at the top."
)

# Never offered the option to stop - see module docstring. The
# verdict above already decided that; this call only produces.
CHILDREN_SYSTEM_PROMPT = (
    "You are raising the resolution of ONE step of an existing plan. "
    "You are given the step, the path of larger steps it sits under, "
    "and how long the whole plan spans. It has already been decided "
    "that this step needs breaking down.\n\n"
    "Go exactly one level down: produce the steps this one is made "
    "of - never their sub-steps, and never a restatement of the step "
    "itself. They must fit inside this step and together account for "
    "it, without extending past it into its siblings' work. Produce "
    "however many actually make sense here, not a fixed count."
)

CHAT_CHILDREN_SYSTEM_PROMPT = (
    "You propose child nodes under ONE project-map node. The user has "
    "been talking about this node and asked for suggestions. Ground "
    "the children in the recent conversation — do not invent a "
    "generic syllabus that ignores what they said. Go exactly one "
    "level down. Produce however many make sense (often 2–4), not a "
    "fixed count. Short labels only."
)

# A safety ceiling only, not a target range - same role as
# calendar.py's MAX_SANE_STEPS.
MAX_SANE_CHILDREN = 20


def _describe_position(label: str, ancestors: list[str], duration: str) -> str:
    """The shared user-content preamble - both calls need the same
    "where does this sit, and inside what span" framing."""
    path = " > ".join([*ancestors, label]) if ancestors else label
    return f"The whole plan spans: {duration}\n\nWhere this step sits: {path}\n\nThe step: {label}"


def is_too_coarse(label: str, ancestors: list[str], duration: str) -> bool:
    """Named, inspectable verdict on whether `label` is still too
    coarse to project an Action from - the explicit reasoning step
    between a step and decomposing it, in the same spirit as
    planner.classify_planability(). Outermost ancestor first."""
    raw = send_message(
        COARSENESS_SYSTEM_PROMPT,
        _describe_position(label, ancestors, duration),
        schema=COARSENESS_SCHEMA,
    )
    return bool(json.loads(raw)["too_coarse"])


def children_of(label: str, ancestors: list[str], duration: str) -> list[str]:
    """The labels of `label`'s immediate children. Assumes the
    is_too_coarse() verdict already came back True - this call is
    never given the option to decline."""
    raw = send_message(
        CHILDREN_SYSTEM_PROMPT,
        _describe_position(label, ancestors, duration),
        schema=CHILDREN_SCHEMA,
    )
    children = json.loads(raw)["children"]
    if len(children) > MAX_SANE_CHILDREN:
        raise ValueError(f"Model returned a runaway child list: {len(children)}")
    return [child["label"] for child in children]


def children_from_conversation(
    label: str,
    ancestors: list[str],
    duration: str,
    conversation: str,
) -> list[str]:
    """Propose children under `label`, grounded in chat — used when
    a focused map node asks for structure ideas. Skips the coarseness
    gate (the request is explicit)."""
    user_content = (
        f"{_describe_position(label, ancestors, duration)}\n\n"
        f"Recent conversation:\n{conversation.strip() or '(none yet)'}\n\n"
        "Propose children under the step that fit what was discussed."
    )
    raw = send_message(
        CHAT_CHILDREN_SYSTEM_PROMPT,
        user_content,
        schema=CHILDREN_SCHEMA,
    )
    children = json.loads(raw)["children"]
    if len(children) > MAX_SANE_CHILDREN:
        raise ValueError(f"Model returned a runaway child list: {len(children)}")
    return [child["label"] for child in children]


def zoom_into(label: str, ancestors: list[str], duration: str) -> list[str]:
    """`label`'s immediate children, or an empty list if it is already
    at a resolution an Action can be projected from."""
    if not is_too_coarse(label, ancestors, duration):
        return []
    return children_of(label, ancestors, duration)
