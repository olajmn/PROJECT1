"""
Parse a pasted outline or ASCII tree into a forest of Step-shaped
labels — no model call. For pasting a structure built elsewhere (e.g.
another LLM's own answer) back into plan.progression, rather than
this app's own construct_progression()/zoom being the only way in.

Tolerant of several styles at once, since a paste's origin is
unknown: markdown bullets ("-", "*", "•"), numbered lists ("1.",
"2)"), this app's own box-drawing export (asciiMap.ts's "└── "/
"├── "/"│"), or plain lines with no marker at all. Depth is read from
each line's raw indentation column, not from matching a single fixed
grammar, so mixed styles and tab/space indentation both work.
"""

import re

_BOX_MARKER = re.compile(r"^(?:└──|├──)\s*")
_BULLET_MARKER = re.compile(r"^[-*•]\s+")
_NUMBERED_MARKER = re.compile(r"^\d+[.)]\s+")
_DECORATION_CHARS = set("│─└├- \t")


def parse_outline(text: str, unwrap: bool = True) -> list[dict]:
    """
    Returns a forest of {"label": str, "children": [...]} nodes,
    oldest/top first. Blank lines and pure connector "air" lines
    (this app's own export pads between siblings with a lone "│") are
    skipped, not read as empty steps.

    If parsing produces exactly one root with children (a title line
    followed by a nested list — a common shape for another LLM's
    answer), and `unwrap` is true (the default), that root is unwrapped
    once and its children are returned instead of it, so the title
    itself doesn't become a spurious top-level step. Only once, not
    repeated: this app's own export nests two labels above real content
    (an id line, then the project name), and unwrapping both would be
    right for reimporting that export - but a generic pasted outline
    can just as easily have a genuinely meaningful two-level chain
    (e.g. "New Hospital" -> "Current State" -> real content), which
    repeated unwrapping would silently discard.

    Whether that single outer line is a throwaway title or content the
    user actually wants kept is not something this parser can know -
    it only sees position (is this line alone at the top?), never
    meaning. `unwrap=False` returns the raw parse, title line included,
    for a caller that wants to show the user both and let them choose
    (see progression_zoom.import_progression_outline()'s own `unwrap`
    parameter and server.py's preview route) rather than this parser
    silently guessing for them.
    """
    stack: list[tuple[int, dict]] = []
    forest: list[dict] = []

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        indent, label = _split_indent_and_label(raw_line)
        if label is None:
            continue

        node = {"label": label, "children": []}
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            stack[-1][1]["children"].append(node)
        else:
            forest.append(node)
        stack.append((indent, node))

    if unwrap and len(forest) == 1 and forest[0]["children"]:
        forest = forest[0]["children"]
    return forest


def _split_indent_and_label(raw_line: str) -> tuple[int, str | None]:
    """One line -> (indent column where content starts, label), or
    (0, None) if the line is blank/pure decoration once a marker is
    stripped. Tab counts as 4 columns, matching this app's own ASCII
    export's stem width."""
    i = 0
    n = len(raw_line)
    indent = 0
    while i < n and raw_line[i] in " \t│":
        indent += 4 if raw_line[i] == "\t" else 1
        i += 1

    rest = raw_line[i:]
    for marker in (_BOX_MARKER, _BULLET_MARKER, _NUMBERED_MARKER):
        match = marker.match(rest)
        if match:
            indent += len(match.group(0))
            rest = rest[match.end():]
            break

    label = rest.strip()
    if not label or set(label) <= _DECORATION_CHARS:
        return 0, None
    return indent, label
