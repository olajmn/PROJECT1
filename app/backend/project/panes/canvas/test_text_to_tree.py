"""
Small, direct checks for text_to_tree.py's most important edge cases
- not a test framework, just asserts run top to bottom.

Run from app/:
    .venv/bin/python -m backend.project.panes.canvas.test_text_to_tree
"""

from backend.project.panes.canvas.text_to_tree import parse_outline


def labels(nodes: list[dict]) -> list:
    """Shorthand: [(label, [child labels...]), ...] for readable asserts."""
    return [(n["label"], labels(n["children"])) for n in nodes]


# Markdown bullets, 2-space indent, unwrapped title line.
MARKDOWN = """
Becoming a developer
- Research
  - List sources
  - Read summaries
- Draft outline
"""
assert labels(parse_outline(MARKDOWN)) == [
    ("Research", [("List sources", []), ("Read summaries", [])]),
    ("Draft outline", []),
], labels(parse_outline(MARKDOWN))

# Numbered list, no title line - two top-level roots, so nothing unwraps.
NUMBERED = """
1. First
2. Second
   1. Nested
"""
assert labels(parse_outline(NUMBERED)) == [
    ("First", []),
    ("Second", [("Nested", [])]),
], labels(parse_outline(NUMBERED))

# This app's own box-drawing export (copyAsText.ts), air lines included -
# only the OUTER wrapper (id line "#41") unwraps; the project name
# ("mfoaiejf") stays as one top-level bead, since unwrapping is only
# ever tried once - see text_to_tree's own docstring for why. Air
# lines are skipped, not read as empty steps.
BOX_DRAWING = (
    "#41\n"
    "└── mfoaiejf\n"
    "    ├── Research\n"
    "    │   ├── List sources\n"
    "    │   │\n"
    "    │   └── Read summaries\n"
    "    │\n"
    "    └── Draft outline\n"
)
assert labels(parse_outline(BOX_DRAWING)) == [
    ("mfoaiejf", [
        ("Research", [("List sources", []), ("Read summaries", [])]),
        ("Draft outline", []),
    ]),
], labels(parse_outline(BOX_DRAWING))

# A genuinely meaningful two-level chain (not just decorative wrapper
# labels) must survive intact - only the outer title unwraps.
MEANINGFUL_NESTING = """
New Hospital
- Current State
  - What is known
  - What is decided
"""
assert labels(parse_outline(MEANINGFUL_NESTING)) == [
    ("Current State", [("What is known", []), ("What is decided", [])]),
], labels(parse_outline(MEANINGFUL_NESTING))

# Flat list, no nesting at all.
FLAT = "- One\n- Two\n- Three\n"
assert labels(parse_outline(FLAT)) == [
    ("One", []), ("Two", []), ("Three", []),
], labels(parse_outline(FLAT))

# Tabs for indentation instead of spaces.
TABS = "Project\n\t- Step A\n\t\t- Sub step\n\t- Step B\n"
assert labels(parse_outline(TABS)) == [
    ("Step A", [("Sub step", [])]),
    ("Step B", []),
], labels(parse_outline(TABS))

# Blank / whitespace-only input has no steps to import.
assert parse_outline("") == []
assert parse_outline("   \n\n\t\n") == []

print("OK - 7 outline case(s) passed")
