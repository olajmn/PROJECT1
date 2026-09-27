"""
Checks the docs/ vault's structural integrity: the expected files
exist (living docs in docs/, finished ones in docs/archive/) and
nothing stray sits alongside them, every [[wikilink]] and
docs/<name>.md-style reference resolves to a file that actually
exists, and each numbered doc's own "# NN — Title" heading matches its
filename.

Deterministic only - no semantic judgment about where content belongs
(see COLLABORATION.md), no automatic rewriting. Companion to
docs_lint.py, which checks prose style rather than structure/references.

Lives at the project root, not under current/ or app/, because docs/
itself is now a shared resource spanning both projects (see README.md)
- one checker, one docs/ vault to be true against, rather than a
separate copy per project drifting out of sync with the other.

Run from the project root (stdlib only, no venv required):
    python3 -m tools.docs_check

Exit code 0 if nothing found, 1 if any problem is reported.
"""

# Contents
#  1. Configuration
#      - EXPECTED_DOCS / ARCHIVED_DOCS
#      - REFERENCE_SCAN_TARGETS
#      - SCANNED_SUFFIXES
#      - WIKILINK_RE / DOC_PATH_RE / H1_NUMBER_RE / FILENAME_NUMBER_RE
#
#  2. Helpers
#      - _iter_files()
#      - _rel()
#
#  3. Checks
#      - check_structure()
#      - check_references()
#      - check_h1_numbering()
#
#  4. Entry Point
#      - main()

import re
import sys
from pathlib import Path

# 1. Configuration

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ARCHIVE = DOCS / "archive"

# The vault's fixed shape - update this list deliberately when a doc
# is genuinely added/renamed, never just to silence a real finding.
EXPECTED_DOCS = [
    "00-project-brief.md",
    "01-research.md",
    "02-product.md",
    "03-architecture.md",
    "04-current-state.md",
    "05-decisions.md",
    # Deliberately unnumbered - a working conceptual model for one
    # subsystem (planning semantics), not one of the seven numbered
    # vault roles above; exempt from check_h1_numbering() for the same
    # reason (its filename carries no NN prefix to check against).
    "planning-model.md",
    # Deliberately unnumbered, same reasoning - a standalone, ever-
    # growing conceptual/speculative document, not one of the seven
    # numbered vault roles (see COLLABORATION.md's doc-role table).
    "concepts.md",
    # Deliberately unnumbered - UI design principles draft (hierarchy,
    # frosted depth, complexity budget).
    "visual-principles.md",
    # Deliberately unnumbered - Projects column roles (sidebar / canvas /
    # chat): what each surface is for vs parked file-folder vision.
    "surfaces.md",
    # TEMPORARY - points salvaged from archived docs, waiting to be moved
    # into their homes. Remove this entry when the file is deleted.
    "TEMP-salvage.md",
]

# Finished or historical docs, kept for reference in docs/archive/
# (COLLABORATION.md's doc-role table: history, not today's truth).
# [[wikilinks]] to them still resolve - Obsidian links by name, not path.
ARCHIVED_DOCS = [
    # The earlier product text (co-build loop, Decide engine), replaced
    # by a short description of today's product 2026-09-27.
    "02-product-v1.md",
    # The original research template (goal-planner competitors, never
    # filled in), replaced by a short node-focused 01 2026-09-27.
    "01-research-v1.md",
    # The original project brief (planner-agent vision), replaced by a
    # short Map+Talk brief 2026-09-27.
    "00-project-brief-v1.md",
    # The original v1->v4 migration decision record (2026-09-11 rename
    # of architecture-v4.md).
    "v4-migration-decision.md",
    # Goal → Project product-then-wire plan; every phase done 2026-09-20.
    "goal-to-project-migration.md",
    # UI visual-reset plan + css/src mirror; cleanup items done.
    "visual-reset.md",
    # Methodology, hypothesis, development log (closed 2026-08-26) and
    # experiments from the prototype 0.1 era.
    "06-development.md",
]

# Files/directories outside docs/ scanned for docs/<name>.md-style
# references (docs/ itself included, for cross-references between
# docs). A curated list of real source areas, not a wildcard project-
# root walk - current/ and app/ each carry their own .venv/ and
# (app/ui) node_modules/, which would otherwise flood this with
# irrelevant .py hits from third-party packages.
REFERENCE_SCAN_TARGETS = [
    "docs",
    "tools",
    "CONVENTIONS.md",
    "COLLABORATION.md",
    "README.md",
    "current/backend",
    "current/frontend",
    "current/tools",
    "current/COLLABORATION.md",
    "current/SESSION-TODO.md",
    "current/README.md",
    "app/backend",
    "app/server.py",
    "app/ui/src",
    "app/README.md",
]
SCANNED_SUFFIXES = {".md", ".py"}

WIKILINK_RE = re.compile(r"\[\[([A-Za-z0-9_-]+)\]\]")
DOC_PATH_RE = re.compile(r"\bdocs/((?:archive/)?[A-Za-z0-9_-]+\.md)\b")
H1_NUMBER_RE = re.compile(r"^#\s+(\d{2})\D")
FILENAME_NUMBER_RE = re.compile(r"^(\d{2})-")

# 2. Helpers


def _iter_files(targets: list[str]) -> list[Path]:
    """Scannable files for `targets`. Directories are walked
    recursively; a bare file is included if its suffix qualifies."""
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

# 3. Checks


def check_structure() -> list[str]:
    """Missing expected docs, and any .md file not on its folder's list
    - catches both a doc that's gone missing and a stray file, in docs/
    (EXPECTED_DOCS) and docs/archive/ (ARCHIVED_DOCS) alike."""
    problems = []
    for folder, listed, name_of_list in (
        (DOCS, EXPECTED_DOCS, "EXPECTED_DOCS"),
        (ARCHIVE, ARCHIVED_DOCS, "ARCHIVED_DOCS"),
    ):
        where = _rel(folder)
        actual = {p.name for p in folder.glob("*.md")}
        for name in listed:
            if name not in actual:
                problems.append(f"{where}/: [MISSING] expected doc not found: {where}/{name}")
        for name in sorted(actual - set(listed)):
            problems.append(f"{where}/{name}: [UNEXPECTED] not listed (see {name_of_list} in tools/docs_check.py)")
    return problems


def check_references() -> list[str]:
    """Every [[wikilink]] and docs/<name>.md-style reference in the
    project resolves to a file that actually exists in docs/. Doesn't
    distinguish "renamed" from "deleted" from "typo" - all three look
    identical here (a reference to a file that isn't there); which one
    it is, and what to do about it, is a human/Claude call."""
    problems = []
    living = list(DOCS.glob("*.md"))
    archived = list(ARCHIVE.glob("*.md"))
    valid_stems = {p.stem for p in living + archived}
    valid_names = {p.name for p in living} | {f"archive/{p.name}" for p in archived}

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
    """Each numbered doc's own "# NN — Title" heading matches its
    filename's number - catches a rename that forgot to update the
    heading. Unnumbered docs (planning-model.md, v4-migration-
    decision.md, concepts.md) have nothing to check against and are
    silently skipped by the filename match below."""
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

# 4. Entry Point


def main() -> int:
    all_problems = check_structure() + check_references() + check_h1_numbering()
    for problem in all_problems:
        print(problem)
    print()
    print(f"{len(all_problems)} problem(s) found.")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
