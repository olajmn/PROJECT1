"""
Checks docs/*.md and every code comment/docstring under backend/ and
devtools/ for the personal-narrative language CONVENTIONS.md's
"Documentation neutrality" rule asks to avoid - the discovery-narrative
style ("found via a real screenshot", "the user's own framing") this
project already moved away from once in code comments (see git
history, "Depersonalize comments: state facts/consequences, not
discovery narrative") and again in docs/ on 2026-08-24. This script
exists so that move doesn't quietly slide back the next time someone
(human or model) writes a new entry.

Unlike tools/architecture_mapper (deliberately generic, no
project-specific knowledge, safe to lift out and reuse elsewhere), this
script IS specific to this project's own house style rule - it doesn't
make sense as a reusable external tool, and isn't trying to be one.

Two confidence tiers, same "code decides, doesn't guess past what it
can verify" reasoning as backend/goals/goal_logic/outcome_classifier.py:

- CONFIRMED: unambiguous regardless of context ("raised in
  conversation", "the user wanted", "found via a real ...").
- REVIEW: "the user's own <noun>" where <noun> isn't already on the
  known-narrative list - genuinely ambiguous ("the user's own device"
  is fine, the product's end-user; "the user's own framing" isn't,
  personal attribution) - same as an unrecognized feedback phrase
  falling back to a safe non-guess rather than the script picking a
  side. Always printed, never counted toward the exit code.

Run from the project root:
    .venv/bin/python3 tools/docs_lint.py
    .venv/bin/python3 tools/docs_lint.py --strict   # REVIEW also fails
    .venv/bin/python3 tools/docs_lint.py docs/03-architecture.md

Exit code 0 if no CONFIRMED hits (REVIEW hits alone don't fail, unless
--strict); exit code 1 if any CONFIRMED hit is found. Safe to wire into
a pre-commit hook later if wanted - not done here, this is a manual
check for now.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories/files this project actually wants checked by default -
# docs/ (the material most likely to be read by someone outside this
# project one day) plus every code comment/docstring under the agent
# and its interface, same scope CONVENTIONS.md's rule names.
DEFAULT_TARGETS = ["docs", "backend", "devtools", "CONVENTIONS.md", "SESSION-TODO.md"]

# Only these extensions are scanned inside a directory target - no
# point walking .venv-style binary/cache noise, and pyc/pycache are
# already excluded by extension alone.
SCANNED_SUFFIXES = {".md", ".py"}

# Confirmed narrative patterns - flagged as an error regardless of
# surrounding context. Each entry is (compiled pattern, short label
# shown in the report).
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

# Ambiguous - "the user's own <noun>" where <noun> wasn't already
# matched above. Could be the product's end-user (fine, e.g. "the
# user's own device") or personal attribution (not fine, e.g. "the
# user's own framing" - already caught above, so won't double-report).
# A human decides which; this script only ever points at the sentence.
REVIEW_PATTERN = re.compile(r"\bthe user'?s own \w+", re.IGNORECASE)


def _iter_files(targets: list[str]) -> list[Path]:
    """
    Every file actually worth scanning, from a list of paths relative
    to the project root - a directory is walked recursively (only
    SCANNED_SUFFIXES kept), a file is included as-is if its suffix
    qualifies. Silently skips a target that doesn't exist, so a
    partial `--paths` list (e.g. only docs/ present in a stripped-down
    checkout) doesn't crash the whole run.
    """
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
            files.extend(sorted(path.rglob(f"*{suffix}")))
    return sorted(set(files))


def _scan_file(path: Path) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    """
    (confirmed, review) for one file - confirmed is a list of (line
    number, matched text, label); review is a list of (line number,
    matched text). Line-by-line, not whole-file regex, so a report can
    always point at exactly one line - good enough for prose that
    rarely spans a match across a line break, and much easier to read
    in the output than a byte offset would be.
    """
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Files/directories to scan, relative to the project root (default: docs/, backend/, devtools/, CONVENTIONS.md, SESSION-TODO.md)",
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
        # relative_to() raises if `path` isn't actually under ROOT (a
        # path outside the project passed explicitly, e.g. for a
        # one-off test) - falls back to the absolute path rather than
        # crashing the whole run over a display detail.
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
