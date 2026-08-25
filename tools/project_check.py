"""
Cheap, deterministic repository orientation - meant to run at the start
of a session (or before a claim about current state matters), so a
session doesn't have to trust its own memory or docs/04-current-state.md's
prose at face value. Reports observable facts: what's changed in git,
which files under the areas docs/04-current-state.md describes are
newer than that file itself, the actual backend/ tree, whether the
core modules still import, and the existing docs checkers' findings.

Interprets nothing. Whether a "newer file" actually means
docs/04-current-state.md is out of date, whether a tree mismatch
matters, what to do about a docs_check/docs_lint finding - all of that
is a human/Claude judgment call, not this script's. See
../COLLABORATION.md for how a session is expected to use this output.

Reuses tools/docs_check.py and tools/docs_lint.py as sub-checks rather
than duplicating their logic - this script is repository-wide
orientation, a layer above them, not a third documentation checker:

    docs_lint.py     -> documentation style
    docs_check.py    -> documentation structural integrity
    project_check.py -> repository/project orientation (this file)
    tests            -> actual runtime behavior (not this file's job -
                         the import check below only confirms a module
                         doesn't raise on import, nothing more)

Run from the project root:
    .venv/bin/python3 -m tools.project_check

Exit code 0 if docs_check.py, docs_lint.py, and the import smoke test
all pass; 1 if any of them found something. The git-status and
newer-than-04-current-state sections are pure information and never
affect the exit code - there's nothing to "pass" or "fail" about an
observable fact.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = ROOT / "docs" / "04-current-state.md"
PYTHON = ROOT / ".venv" / "bin" / "python3"

# Areas docs/04-current-state.md actually describes - not all of the
# repo, just the parts relevant to whether it might need a fresh look.
RELEVANT_AREAS = ["backend", "devtools", "docs"]

# Kept small and explicit rather than dynamically discovered - an
# orientation smoke test, not a dependency graph. Add a module here
# only if it's a real entry point worth confirming still imports.
SMOKE_IMPORT_MODULES = [
    "backend.planning.plan",
    "backend.goals.goal_logic.goal",
    "backend.infrastructure.data_persistence",
    "devtools.app",
]


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess from the project root, return (exit code,
    combined stdout+stderr) - never raises; a failing sub-check is
    itself part of the report, not a crash. Only trailing whitespace
    is trimmed - `git status --porcelain`'s status columns are
    position-sensitive, so a leading-whitespace-eating `.strip()` on
    the combined output would corrupt its first line."""
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).rstrip()


def git_status() -> list[str]:
    """Every changed/untracked path from `git status --porcelain`,
    relative to the repo root - the raw fact, not an interpretation."""
    code, output = _run(["git", "status", "--porcelain"])
    if code != 0 or not output:
        return []
    # Porcelain format is "XY path" - the path starts after the two
    # status characters and a space.
    return [line[3:].strip() for line in output.splitlines()]


def files_newer_than_current_state() -> list[str]:
    """Every file under RELEVANT_AREAS whose mtime is newer than
    docs/04-current-state.md's own mtime. Purely observable - doesn't
    claim this means the doc is stale (a file can be touched without
    its meaning changing, and the reverse); that judgment is left to
    whoever reads the report. mtime, not `git log`, because this
    project's docs/ work is routinely uncommitted for a whole session
    at a time - `git log` sees nothing for a file that was never
    committed, mtime always does."""
    if not CURRENT_STATE.exists():
        return []
    reference = CURRENT_STATE.stat().st_mtime
    newer = []
    for area in RELEVANT_AREAS:
        area_path = ROOT / area
        if not area_path.exists():
            continue
        for path in area_path.rglob("*"):
            if not path.is_file() or path == CURRENT_STATE:
                continue
            if "__pycache__" in path.parts or ".obsidian" in path.parts:
                continue
            if path.stat().st_mtime > reference:
                newer.append(str(path.relative_to(ROOT)))
    return sorted(newer)


def backend_tree() -> list[str]:
    """The actual backend/ directory tree, one relative path per line -
    a plain fact to hold up against whatever docs/04-current-state.md's
    own "What exists" tree currently says. This script doesn't parse
    or diff the doc's prose tree itself - reading the doc and noticing
    a mismatch is exactly the kind of judgment call left to whoever
    reads this report, not something to automate here."""
    backend = ROOT / "backend"
    if not backend.exists():
        return []
    return sorted(
        str(p.relative_to(ROOT)) + "/"
        for p in backend.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    )


def import_smoke_test() -> list[str]:
    """Each module in SMOKE_IMPORT_MODULES, imported in its own
    subprocess (one bad import can't take down the rest) - failures
    only, since a clean import needs no report. Confirms importability,
    not behavior - see this file's own docstring for why that's the
    deliberate boundary."""
    failures = []
    for module in SMOKE_IMPORT_MODULES:
        code, output = _run([str(PYTHON), "-c", f"import {module}"])
        if code != 0:
            last_line = output.splitlines()[-1] if output else "failed, no output captured"
            failures.append(f"{module}: {last_line}")
    return failures


def run_tool(module: str) -> tuple[int, str]:
    """Run an existing tools/ script as a subprocess, reused as-is
    rather than reimplemented."""
    return _run([str(PYTHON), "-m", f"tools.{module}"])


def main() -> int:
    exit_code = 0

    print("=== git status ===")
    changed = git_status()
    if changed:
        for path in changed:
            print(f"  {path}")
    else:
        print("  clean")

    print()
    print("=== files newer than docs/04-current-state.md ===")
    newer = files_newer_than_current_state()
    if newer:
        for path in newer:
            print(f"  {path}")
        print()
        print("  (observed fact only - whether this means")
        print("  docs/04-current-state.md needs a fresh look is a")
        print("  judgment call, not this script's.)")
    else:
        print("  none - docs/04-current-state.md is the most recently")
        print("  touched file among the areas it describes")

    print()
    print("=== backend/ tree (compare against docs/04-current-state.md § What exists) ===")
    for line in backend_tree():
        print(f"  {line}")

    print()
    print("=== import smoke test ===")
    failures = import_smoke_test()
    if failures:
        for failure in failures:
            print(f"  FAILED: {failure}")
        exit_code = 1
    else:
        print("  all modules import cleanly")

    print()
    print("=== tools/docs_check.py ===")
    code, output = run_tool("docs_check")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    print()
    print("=== tools/docs_lint.py ===")
    code, output = run_tool("docs_lint")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
