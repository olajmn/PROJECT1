"""
Cheap, deterministic repository orientation - meant to run at the start
of a session, so it doesn't have to trust its own memory or
docs/04-current-state.md's prose at face value. Reports observable
facts: git status, files newer than docs/04-current-state.md, the
actual backend/ and frontend/ trees, whether the core modules still
import, code-level hygiene (pyflakes, stale backend/frontend path
mentions, modules with no inbound import), the architecture_foundation/
skeleton (when present), and the existing docs checkers' findings.

Interprets nothing about content or correctness - every finding is
left for a human/Claude to judge. See ../COLLABORATION.md for how a
session is expected to use this output. Wraps docs_check.py,
docs_lint.py, and pyflakes as sub-checks rather than duplicating their
logic.

Run from the project root:
    .venv/bin/python3 -m tools.project_check

Exit code 0 if docs_check.py, docs_lint.py, pyflakes, the import smoke
test, and the architecture_foundation/ skeleton check all pass; 1 if
any of them found something. Every other section is pure information
and never affects the exit code.
"""

# Contents
#  1. Configuration
#      - ROOT / CURRENT_STATE / PYTHON
#      - ARCHITECTURE_SKELETON
#      - ARCHITECTURE_SKELETON_CORE_DOCS
#      - RELEVANT_AREAS
#      - SMOKE_IMPORT_MODULES
#
#  2. Checks
#      - _run()
#      - git_status()
#      - files_newer_than_current_state()
#      - directory_tree()
#      - import_smoke_test()
#      - run_tool()
#      - run_pyflakes()
#      - CODE_PATH_RE / STALE_PATH_SCAN_AREAS
#      - stale_code_path_mentions()
#      - modules_with_no_inbound_import()
#      - architecture_skeleton_check()
#
#  3. Entry Point
#      - main()

import re
import subprocess
import sys
from pathlib import Path

# 1. Configuration

ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = ROOT / "docs" / "04-current-state.md"
PYTHON = ROOT / ".venv" / "bin" / "python3"

# Not present on every branch (e.g. absent on main) - see
# architecture_skeleton_check() for why that's a silent skip.
ARCHITECTURE_SKELETON = ROOT / "architecture_foundation"

# Docs every architecture_foundation/ is expected to have at its root.
ARCHITECTURE_SKELETON_CORE_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "COMPONENT_MAP.md",
    "DECISIONS.md",
    "ROADMAP.md",
]

# Areas docs/04-current-state.md actually describes.
RELEVANT_AREAS = ["backend", "frontend", "docs"]

# Real entry points worth confirming still import - not dynamically
# discovered.
SMOKE_IMPORT_MODULES = [
    "backend.goals.plan.planner",
    "backend.goals.goal.resolver",
    "backend.infrastructure.data_persistence",
    "frontend.app",
]


# 2. Checks


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess from the project root; never raises, since a
    failing sub-check is itself part of the report. Trims only
    trailing whitespace - `git status --porcelain`'s columns are
    position-sensitive, so `.strip()` would corrupt a leading status
    character."""
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).rstrip()


def git_status() -> list[str]:
    """Changed/untracked paths from `git status --porcelain`, relative
    to the repo root."""
    code, output = _run(["git", "status", "--porcelain"])
    if code != 0 or not output:
        return []
    # Porcelain format is "XY path" - the path starts after the two
    # status characters and a space.
    return [line[3:].strip() for line in output.splitlines()]


def files_newer_than_current_state() -> list[str]:
    """Files under RELEVANT_AREAS newer than docs/04-current-state.md.

    Uses mtime rather than git history because docs/ work is often
    uncommitted for a whole session - `git log` sees nothing for a
    file that was never committed, mtime always does. Observable
    signal only, not proof the doc is stale: touching a file doesn't
    guarantee its meaning changed, and vice versa."""
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


def directory_tree(area: str) -> list[str]:
    """Directory tree for `area` (e.g. "backend", "frontend"), to
    compare against docs/04-current-state.md's "Project Structure"
    section for that area."""
    area_path = ROOT / area
    if not area_path.exists():
        return []
    return sorted(
        str(p.relative_to(ROOT)) + "/"
        for p in area_path.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    )


def import_smoke_test() -> list[str]:
    """Imports each module in SMOKE_IMPORT_MODULES in its own
    subprocess, so one bad import can't take down the rest. Reports
    failures only. Confirms importability, not runtime behavior."""
    failures = []
    for module in SMOKE_IMPORT_MODULES:
        code, output = _run([str(PYTHON), "-c", f"import {module}"])
        if code != 0:
            last_line = output.splitlines()[-1] if output else "failed, no output captured"
            failures.append(f"{module}: {last_line}")
    return failures


def run_tool(module: str) -> tuple[int, str]:
    """Run an existing tools/ script as a subprocess."""
    return _run([str(PYTHON), "-m", f"tools.{module}"])


def run_pyflakes() -> tuple[int, str]:
    """Run pyflakes (already a project dependency) against backend/
    and frontend/."""
    return _run([str(PYTHON), "-m", "pyflakes", "backend", "frontend"])


# A backend/... or frontend/...-looking .py path mentioned in a
# comment, docstring, or docs/ prose.
CODE_PATH_RE = re.compile(r"\b(?:backend|frontend)/[A-Za-z0-9_/().-]+\.py\b")

# Where to scan for CODE_PATH_RE mentions: .py under backend/frontend/
# tools, .md under docs/.
STALE_PATH_SCAN_AREAS = [
    ("backend", "*.py"),
    ("frontend", "*.py"),
    ("tools", "*.py"),
    ("docs", "*.md"),
]


def stale_code_path_mentions() -> list[str]:
    """Every backend/... or frontend/...-looking .py path mentioned
    anywhere under backend/, frontend/, tools/, or docs/ that doesn't
    resolve to a real file. Doesn't distinguish a genuine leftover
    reference from a docstring or doc deliberately narrating "moved
    from X" as history."""
    stale = []
    for area, pattern in STALE_PATH_SCAN_AREAS:
        area_path = ROOT / area
        if not area_path.exists():
            continue
        for path in sorted(area_path.rglob(pattern)):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in CODE_PATH_RE.finditer(line):
                    referenced = match.group(0)
                    if not (ROOT / referenced).exists():
                        stale.append(f"{path.relative_to(ROOT)}:{line_number}: {referenced}")
    return stale


def modules_with_no_inbound_import() -> list[str]:
    """Backend modules (excluding __init__.py) that no other .py file
    under backend/, frontend/, or tools/ appears to mention by dotted
    path or bare filename. A plain text search, not real import-graph
    analysis - many hits here are legitimate entry points (see
    SMOKE_IMPORT_MODULES) rather than dead code."""
    py_files = [
        p
        for area in ("backend", "frontend", "tools")
        for p in (ROOT / area).rglob("*.py")
        if "__pycache__" not in p.parts
    ]
    contents = {p: p.read_text(encoding="utf-8", errors="replace") for p in py_files}
    backend_modules = [
        p
        for p in (ROOT / "backend").rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    ]

    orphans = []
    for module_path in backend_modules:
        dotted = ".".join(module_path.relative_to(ROOT).with_suffix("").parts)
        base = module_path.stem
        referenced = any(
            dotted in text or f"import {base}" in text or f".{base}" in text
            for other_path, text in contents.items()
            if other_path != module_path
        )
        if not referenced:
            orphans.append(str(module_path.relative_to(ROOT)))
    return sorted(orphans)


def architecture_skeleton_check() -> list[str] | None:
    """
    Structural check for architecture_foundation/. Returns None if
    ARCHITECTURE_SKELETON doesn't exist at all ("nothing to check
    here"), distinct from an empty list ("checked, found nothing
    wrong").

    Checks only that the skeleton's shape hasn't eroded: the five core
    docs (ARCHITECTURE_SKELETON_CORE_DOCS) exist and are non-empty,
    and every directory under architecture_foundation/ has its own
    non-empty README.md. Component folders are discovered by walking
    the tree, not hardcoded.

    Deliberately does not check whether a component's status
    (CURRENT/NEXT/FUTURE/EXPLORATORY) is accurate or its content is
    correct - "does the structure exist" is checkable; "is the
    architecture right" isn't.
    """
    if not ARCHITECTURE_SKELETON.exists():
        return None

    problems = []
    for doc_name in ARCHITECTURE_SKELETON_CORE_DOCS:
        path = ARCHITECTURE_SKELETON / doc_name
        if not path.exists():
            problems.append(f"missing core doc: {path.relative_to(ROOT)}")
        elif path.stat().st_size == 0:
            problems.append(f"empty core doc: {path.relative_to(ROOT)}")

    for dir_path in sorted(ARCHITECTURE_SKELETON.rglob("*")):
        if not dir_path.is_dir() or "__pycache__" in dir_path.parts:
            continue
        readme = dir_path / "README.md"
        if not readme.exists():
            problems.append(f"component folder missing README.md: {readme.relative_to(ROOT)}")
        elif readme.stat().st_size == 0:
            problems.append(f"empty README.md: {readme.relative_to(ROOT)}")

    return problems


# 3. Entry Point


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
    print("=== backend/ tree (compare against docs/04-current-state.md § 1. Project Structure) ===")
    for line in directory_tree("backend"):
        print(f"  {line}")

    print()
    print("=== frontend/ tree (compare against docs/04-current-state.md § 1. Project Structure) ===")
    for line in directory_tree("frontend"):
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
    print("=== pyflakes (backend/, frontend/) ===")
    code, output = run_pyflakes()
    print(output if output else "  no issues found")
    if code != 0:
        exit_code = 1

    print()
    print("=== stale backend/frontend .py path mentions ===")
    stale_paths = stale_code_path_mentions()
    if stale_paths:
        for line in stale_paths:
            print(f"  {line}")
        print()
        print("  (observed fact only - a dated docstring narrating a")
        print("  past move is expected to show up here too; whether a")
        print("  given hit is a leftover bug or intentional history is")
        print("  a judgment call, not this script's.)")
    else:
        print("  none")

    print()
    print("=== backend/ modules with no detected inbound import ===")
    orphans = modules_with_no_inbound_import()
    if orphans:
        for path in orphans:
            print(f"  {path}")
        print()
        print("  (observed fact only - a module can legitimately have")
        print("  no inbound import because it's a command-line entry")
        print("  point (see SMOKE_IMPORT_MODULES above) rather than")
        print("  dead code; that judgment is not this script's.)")
    else:
        print("  none")

    print()
    print("=== architecture_foundation/ skeleton check ===")
    skeleton_problems = architecture_skeleton_check()
    if skeleton_problems is None:
        print("  architecture_foundation/ not present on this branch - skipping")
    elif skeleton_problems:
        for problem in skeleton_problems:
            print(f"  {problem}")
        exit_code = 1
    else:
        print("  all core docs and component READMEs present")

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
