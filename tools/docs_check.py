"""
Checks the docs/ vault's structural integrity: the expected 00-06 files
exist and nothing stray sits alongside them, every [[wikilink]] and
docs/<NN>-<name>.md-style reference across the project resolves to a file
that actually exists, and each doc's own "# NN — Title" heading matches
its filename.

Deterministic only - no semantic judgment about where content belongs
(that stays a human/Claude decision, see ../COLLABORATION.md) and no
automatic rewriting or moving of anything. Companion to
tools/docs_lint.py (prose style/personal-narrative language) - a
different concern, structure and references rather than language, so
kept as its own script rather than folded into that one.

Run from the project root:
    .venv/bin/python3 -m tools.docs_check

Exit code 0 if nothing found, 1 if any problem is reported.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# The vault's fixed shape, as settled 2026-08-25 - update this list
# deliberately when a doc is genuinely added/renamed, never just to
# silence a real finding.
EXPECTED_DOCS = [
    "00-project-brief.md",
    "01-research.md",
    "02-product.md",
    "03-architecture.md",
    "04-current-state.md",
    "05-decisions.md",
    "06-development.md",
]

# Files outside docs/ worth scanning for docs/<NN>-<name>.md-style
# references - same scope docs_lint.py already uses for its own scan.
# docs/ itself is scanned too (for cross-references between docs), via
# the same walk.
REFERENCE_SCAN_TARGETS = ["docs", "backend", "frontend", "tools", "CONVENTIONS.md", "SESSION-TODO.md"]
SCANNED_SUFFIXES = {".md", ".py"}

WIKILINK_RE = re.compile(r"\[\[([A-Za-z0-9_-]+)\]\]")
DOC_PATH_RE = re.compile(r"\bdocs/([A-Za-z0-9_-]+\.md)\b")
H1_NUMBER_RE = re.compile(r"^#\s+(\d{2})\D")
FILENAME_NUMBER_RE = re.compile(r"^(\d{2})-")


def _iter_files(targets: list[str]) -> list[Path]:
    """Every file worth scanning, from paths relative to the project
    root - a directory is walked recursively (only SCANNED_SUFFIXES
    kept), a file is included as-is if its suffix qualifies. Same
    shape as docs_lint.py's own helper, kept separate rather than
    imported - the two scripts check different things and aren't
    meant to share more than the pattern."""
    files: list[Path] = []
    for target in targets:
        path = ROOT / target
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in SCANNED_SUFFIXES:
                files.append(path)
            continue
        for suffix in SCANNED_SUFFIXES:
            files.extend(sorted(path.rglob(f"*{suffix}")))
    return sorted(set(files))


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def check_structure() -> list[str]:
    """Missing expected docs, and any docs/*.md file not on the
    expected list - catches both a doc that's gone missing and a
    stray/resurrected file (an old numbered doc, a stray day-file)
    sitting next to the real seven."""
    problems = []
    actual = {p.name for p in DOCS.glob("*.md")}
    expected = set(EXPECTED_DOCS)
    for name in EXPECTED_DOCS:
        if name not in actual:
            problems.append(f"docs/: [MISSING] expected doc not found: docs/{name}")
    for name in sorted(actual - expected):
        problems.append(f"docs/{name}: [UNEXPECTED] not one of the 7 expected docs (see EXPECTED_DOCS in tools/docs_check.py)")
    return problems


def check_references() -> list[str]:
    """Every [[wikilink]] and docs/<NN>-<name>.md-style reference,
    anywhere in the project, resolves to a file that actually exists
    in docs/ today. Doesn't distinguish "renamed" from "deleted" from
    "typo" - all three look identical from here (a reference to a
    file that isn't there), and that's the only thing worth reporting
    deterministically; which of the three it is, and what to do about
    it, is a human/Claude call."""
    problems = []
    valid_stems = {p.stem for p in DOCS.glob("*.md")}
    valid_names = {p.name for p in DOCS.glob("*.md")}

    for path in _iter_files(["docs"]):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in WIKILINK_RE.finditer(line):
                target = match.group(1)
                if target not in valid_stems:
                    problems.append(f"{_rel(path)}:{line_number}: [BROKEN WIKILINK] [[{target}]]")

    for path in _iter_files(REFERENCE_SCAN_TARGETS):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in DOC_PATH_RE.finditer(line):
                target = match.group(1)
                if target not in valid_names:
                    problems.append(f"{_rel(path)}:{line_number}: [BROKEN REFERENCE] docs/{target}")
    return problems


def check_h1_numbering() -> list[str]:
    """Each doc's own "# NN — Title" heading names the same number as
    its filename - cheap, mechanical, and catches a real class of
    mistake (a rename that forgot to update the file's own heading)."""
    problems = []
    for path in sorted(DOCS.glob("*.md")):
        filename_match = FILENAME_NUMBER_RE.match(path.name)
        if not filename_match:
            continue
        expected_number = filename_match.group(1)
        text = path.read_text(encoding="utf-8", errors="replace")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        h1_match = H1_NUMBER_RE.match(first_line)
        if not h1_match:
            problems.append(f"{_rel(path)}:1: [H1 MISMATCH] heading doesn't start with '# NN' at all: {first_line!r}")
        elif h1_match.group(1) != expected_number:
            problems.append(
                f"{_rel(path)}:1: [H1 MISMATCH] filename says {expected_number!r}, heading says {h1_match.group(1)!r}"
            )
    return problems


def main() -> int:
    all_problems = check_structure() + check_references() + check_h1_numbering()
    for problem in all_problems:
        print(problem)
    print()
    print(f"{len(all_problems)} problem(s) found.")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
