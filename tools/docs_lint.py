"""
Checks docs/*.md and code comments/docstrings under current/ and
app/ for personal-narrative language (see CONVENTIONS.md's
"Documentation neutrality" rule).

Two confidence tiers: CONFIRMED patterns are unambiguous regardless of
context and fail the run; REVIEW patterns are genuinely ambiguous,
always printed, but never fail on their own.

Lives at the project root, not under current/ or app/, same reasoning
as tools/docs_check.py: docs/ and CONVENTIONS.md are shared resources
spanning both projects, not owned by either one.

Run from the project root (stdlib only, no venv required):
    python3 tools/docs_lint.py
    python3 tools/docs_lint.py --strict   # REVIEW also fails
    python3 tools/docs_lint.py docs/03-architecture.md

Exit code 0 if no CONFIRMED hits (REVIEW alone doesn't fail unless
--strict); 1 if any CONFIRMED hit is found.
"""

# Contents
#  1. Configuration
#      - ROOT
#      - DEFAULT_TARGETS
#      - ARCHIVE
#      - SCANNED_SUFFIXES
#      - CONFIRMED_PATTERNS
#      - REVIEW_PATTERN
#
#  2. Helpers
#      - _iter_files()
#      - _scan_file()
#
#  3. Entry Point
#      - main()

import argparse
import re
import sys
from pathlib import Path

# 1. Configuration

ROOT = Path(__file__).resolve().parent.parent

# Default scan targets - same scope CONVENTIONS.md's rule names, and
# the same curated-areas reasoning as tools/docs_check.py's
# REFERENCE_SCAN_TARGETS (avoids walking into current/.venv,
# app/.venv, and app/ui/node_modules).
DEFAULT_TARGETS = [
    "docs",
    "CONVENTIONS.md",
    "COLLABORATION.md",
    "current/backend",
    "current/frontend",
    "current/SESSION-TODO.md",
    "app/backend",
    "app/server.py",
    "app/ui/src",
]

# Not walked: optional and unmaintained, same as tools/docs_check.py's
# ARCHIVE. A file in it passed explicitly is still scanned.
ARCHIVE = ROOT / "docs" / "archive"

# Extensions scanned inside a directory target.
SCANNED_SUFFIXES = {".md", ".py", ".ts"}

# CONFIRMED patterns - flagged regardless of context. Each entry is
# (pattern, label shown in the report).
_CONFIRMED_PATTERNS = [
    (r"\braised in conversation\b", "discovery narrative"),
    (r"\bthe user (wanted|explicitly asked|explicitly said|explicitly stated)\b", "personal attribution"),
    (r"\bfound via a real\b", "discovery narrative"),
    (r"\b(discovered|noticed) via\b", "discovery narrative"),
    (r"\bnoticed while (building|testing|using)\b", "discovery narrative"),
    (
        r"\bthe user'?s own (framing|analogy|analogies|estimate|instinct|"
        r"courtroom analogy|stated reason|opinion|idea|take on|view on)\b",
        "personal attribution",
    ),
    (r"\bI (found|noticed|think|feel|felt)\b", "first-person narrative"),
]
CONFIRMED_PATTERNS = [(re.compile(p, re.IGNORECASE), label) for p, label in _CONFIRMED_PATTERNS]

# Ambiguous - "the user's own <noun>" where <noun> isn't already
# matched above. Could be the product's end-user (fine, e.g. "the
# user's own device") or personal attribution (not fine, e.g. "the
# user's own framing"). A human decides which; this only points at
# the sentence.
REVIEW_PATTERN = re.compile(r"\bthe user'?s own \w+", re.IGNORECASE)

# 2. Helpers


def _iter_files(targets: list[str]) -> list[Path]:
    """Scannable files for `targets`. Directories are walked
    recursively; a target that doesn't exist is skipped."""
    files = []
    for target in targets:
        path = ROOT / target
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in SCANNED_SUFFIXES:
                files.append(path)
            continue
        for suffix in SCANNED_SUFFIXES:
            files.extend(f for f in path.rglob(f"*{suffix}") if ARCHIVE not in f.parents)
    return sorted(set(files))


def _scan_file(path: Path) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    """(confirmed, review) for one file: confirmed is (line, text,
    label) tuples, review is (line, text) tuples. Matching is
    line-by-line so a hit can be reported against a single line
    number."""
    confirmed: list[tuple[int, str, str]] = []
    review: list[tuple[int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        line_had_confirmed_hit = False
        for pattern, label in CONFIRMED_PATTERNS:
            match = pattern.search(line)
            if match:
                confirmed.append((line_number, match.group(0), label))
                line_had_confirmed_hit = True
        # Only checked when nothing on this line already triggered a
        # CONFIRMED hit - "the user's own framing" would otherwise show
        # up twice, once per tier, for the exact same words.
        if not line_had_confirmed_hit:
            match = REVIEW_PATTERN.search(line)
            if match:
                review.append((line_number, match.group(0)))
    return confirmed, review

# 3. Entry Point


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Files/directories to scan, relative to the project root (default: docs/, current/ and app/ backend/frontend, CONVENTIONS.md, COLLABORATION.md)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail (exit 1) on REVIEW hits, not just CONFIRMED ones",
    )
    args = parser.parse_args()

    total_confirmed = 0
    total_review = 0
    for path in _iter_files(args.paths):
        confirmed, review = _scan_file(path)
        # relative_to() raises if `path` isn't under ROOT (e.g. a path
        # passed explicitly for a one-off test) - falls back to the
        # absolute path rather than crashing over a display detail.
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        for line_number, matched, label in confirmed:
            print(f"{rel}:{line_number}: [CONFIRMED - {label}] {matched!r}")
        for line_number, matched in review:
            print(f"{rel}:{line_number}: [REVIEW - check by hand] {matched!r}")
        total_confirmed += len(confirmed)
        total_review += len(review)

    print()
    print(f"{total_confirmed} confirmed, {total_review} for review.")
    if total_confirmed:
        return 1
    if args.strict and total_review:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
