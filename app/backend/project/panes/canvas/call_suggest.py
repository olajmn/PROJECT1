"""
One level of decomposition, on demand: given a map node and the path
it sits under, raise the resolution of that one point — never a
whole sub-tree. This is docs/planning-model.md § Decomposition /
zoom; that section deliberately does NOT decide whether the finer
content is persisted, so nothing here writes anything.

Asking for one flat level is easier for the local model than asking
for a nested one, not harder: CHILDREN_SCHEMA has no recursion in it,
and Ollama constrains generation to the schema rather than only to
valid JSON syntax the way format="json" does. Depth grows by calling
zoom_into() again on a child, so no single response ever carries a
tree.

Suggest does not read leftover project `duration`. A fixed
grounding line is enough for the model preamble.

TWO calls, deliberately - the depth verdict is asked separately from
the decomposition, and measured to need to be. Asked to judge and
decompose at once, the model always took the cheap branch: given a
schema where "no children" was valid, it returned empty for all five
test steps including "climb Mount Everest" over 18 months. Asked to
do nothing but judge (is_too_coarse()), it was unanimous and correct
on five of seven cases, and when forbidden to stop it decomposed
well. It can do either job; it collapses when one call has to do
both.

Prompts and schemas live in model/brief/suggest.py.
"""

import json

from backend.model.brief.suggest import (
    CHAT_CHILDREN_SYSTEM_PROMPT,
    CHILDREN_SCHEMA,
    CHILDREN_SYSTEM_PROMPT,
    COARSENESS_SCHEMA,
    COARSENESS_SYSTEM_PROMPT,
    describe_position,
)
from backend.model.client import send_message

# A safety ceiling only, not a target range.
MAX_SANE_CHILDREN = 20


def is_too_coarse(label: str, ancestors: list[str]) -> bool:
    """Named, inspectable verdict on whether `label` is still too
    coarse to project an Action from - the explicit reasoning step
    between a step and decomposing it. Outermost ancestor first."""
    raw = send_message(
        COARSENESS_SYSTEM_PROMPT,
        describe_position(label, ancestors),
        schema=COARSENESS_SCHEMA,
    )
    return bool(json.loads(raw)["too_coarse"])


def children_of(label: str, ancestors: list[str]) -> list[str]:
    """The labels of `label`'s immediate children. Assumes the
    is_too_coarse() verdict already came back True - this call is
    never given the option to decline."""
    raw = send_message(
        CHILDREN_SYSTEM_PROMPT,
        describe_position(label, ancestors),
        schema=CHILDREN_SCHEMA,
    )
    children = json.loads(raw)["children"]
    if len(children) > MAX_SANE_CHILDREN:
        raise ValueError(f"Model returned a runaway child list: {len(children)}")
    return [child["label"] for child in children]


def children_from_conversation(
    label: str,
    ancestors: list[str],
    conversation: str,
) -> list[str]:
    """Propose children under `label`, grounded in chat — used when
    a focused map node asks for structure ideas. Skips the coarseness
    gate (the request is explicit)."""
    user_content = (
        f"{describe_position(label, ancestors)}\n\n"
        f"Recent conversation:\n{conversation.strip() or '(none yet)'}\n\n"
        "Propose children under the node that fit what was discussed."
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


def zoom_into(label: str, ancestors: list[str]) -> list[str]:
    """`label`'s immediate children, or an empty list if it is already
    at a resolution an Action can be projected from."""
    if not is_too_coarse(label, ancestors):
        return []
    return children_of(label, ancestors)
