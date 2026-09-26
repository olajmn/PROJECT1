"""Suggest / zoom — prompts, schemas, and the position preamble the
model gets. Call sites in canvas/call_suggest.py own the call + parse.
"""

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
    "You judge ONE thing about a node on a project map: is it still "
    "too coarse to be a meaningful next unit of work, or is it already "
    "at a resolution where a concrete next action could be projected "
    "from it directly?\n\n"
    "Set too_coarse to true if the node still needs breaking down "
    "before anyone could act on it. Set it to false if a person could "
    "already project a concrete next action straight from it.\n\n"
    "Judge the node at the position it actually sits in - a node deep "
    "under several larger ones is usually nearer to being actionable "
    "than the project at the top."
)

# Never offered the option to stop - see call_suggest module docstring.
# The verdict above already decided that; this call only produces.
CHILDREN_SYSTEM_PROMPT = (
    "You are raising the resolution of ONE node on a project map. "
    "You are given the node and the path of larger nodes it sits under. "
    "It has already been decided that this node needs breaking down.\n\n"
    "Go exactly one level down: produce the nodes this one is made "
    "of - never their sub-nodes, and never a restatement of the node "
    "itself. They must fit inside this node and together account for "
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

_GROUNDING = (
    "no fixed timeframe — a few next units of work only, "
    "not a full syllabus"
)


def describe_position(label: str, ancestors: list[str]) -> str:
    """Where this node sits on the map. No leftover project span."""
    path = " > ".join([*ancestors, label]) if ancestors else label
    return (
        f"{_GROUNDING}\n\n"
        f"Where this sits on the map: {path}\n\n"
        f"The node: {label}"
    )
