"""
Cheap, deterministic repository orientation - meant to run at the start
of a session, so it doesn't have to trust its own memory or
docs/04-current-state.md's prose at face value. Reports observable
facts: git status, files newer than docs/04-current-state.md, agent/'s
actual backend/ tree, whether the core modules still import,
code-level hygiene (pyflakes, stale backend/ path mentions, modules
with no inbound import), and this same tools/'s docs_check.py/
docs_lint.py findings.

Interprets nothing about content or correctness - every finding is
left for a human/Claude to judge. See ../COLLABORATION.md for how a
session is expected to use this output. Wraps docs_check.py and
docs_lint.py (this same directory - one shared tools/ for the whole
project, not a per-project copy) and pyflakes as sub-checks rather
than duplicating their logic.

Run from the project root, but against agent/'s own venv (this is the
only project this script's backend/import checks target):
    agent/.venv/bin/python3 -m tools.project_check

Exit code 0 if docs_check.py, docs_lint.py, pyflakes, and the import
smoke test all pass; 1 if any of them found something. Every other
section is pure information and never affects the exit code.
"""

# Contents
#  1. Configuration
#      - PROJECT_ROOT / AGENT_ROOT / DOCS_ROOT / CURRENT_STATE / PYTHON
#      - RELEVANT_AREAS
#      - PY_SCAN_AREAS / PY_SCAN_FILES
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
#      - CODE_PATH_RE / STALE_PATH_SCAN_TARGETS
#      - stale_code_path_mentions()
#      - modules_with_no_inbound_import()
#
#  3. Entry Point
#      - main()

import re
import subprocess
import sys
from pathlib import Path

# 1. Configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # PROJECT1/ - tools/ lives directly under it
AGENT_ROOT = PROJECT_ROOT / "agent"
DOCS_ROOT = PROJECT_ROOT / "docs"
CURRENT_STATE = DOCS_ROOT / "04-current-state.md"
PYTHON = AGENT_ROOT / ".venv" / "bin" / "python3"

# Areas docs/04-current-state.md actually describes, each an absolute
# path since docs/ is shared at the project root while backend/ lives
# under agent/ itself. No "frontend" yet - see docs/04-current-state.md
# § 6 for what agent/ hasn't carried over from current/.
RELEVANT_AREAS = [AGENT_ROOT / "backend", DOCS_ROOT]

# .py corpus for stale-path and orphan-import scanning: backend/
# recursively, plus the top-level entry points that import from it -
# cli.py/server.py aren't under backend/, but are exactly where
# backend.llm1/llm2/llm3/planning are actually wired together (see
# docs/04-current-state.md § 3.ii), so excluding them would make every
# one of those modules look orphaned.
PY_SCAN_AREAS = ["backend"]
PY_SCAN_FILES = ["cli.py", "server.py"]

# Real entry points worth confirming still import - not dynamically
# discovered.
SMOKE_IMPORT_MODULES = [
    "backend.planning.plan.planner",
    "backend.planning.goal.resolver",
    "backend.infrastructure.data_persistence",
    "backend.llm1.interface",
    "backend.llm2.parser",
    "backend.llm3.select",
    "backend.manifestation",
    "backend.module_library.modules",
    "cli",
    "server",
]


# 2. Checks


def _run(cmd: list[str], cwd: Path = AGENT_ROOT) -> tuple[int, str]:
    """Run a subprocess; never raises, since a failing sub-check is
    itself part of the report. Trims only trailing whitespace - `git
    status --porcelain`'s columns are position-sensitive, so
    `.strip()` would corrupt a leading status character."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).rstrip()


def git_status() -> list[str]:
    """Changed/untracked paths from `git status --porcelain`, relative
    to the repo root (the whole PROJECT1 checkout, not just agent/ -
    one git repository spans both)."""
    code, output = _run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT)
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
    for area_path in RELEVANT_AREAS:
        if not area_path.exists():
            continue
        for path in area_path.rglob("*"):
            if not path.is_file() or path == CURRENT_STATE:
                continue
            if "__pycache__" in path.parts or ".obsidian" in path.parts:
                continue
            if path.stat().st_mtime > reference:
                newer.append(str(path.relative_to(PROJECT_ROOT)))
    return sorted(newer)


def directory_tree(area_path: Path) -> list[str]:
    """Directory tree for `area_path`, to compare against
    docs/04-current-state.md's "Project Structure" section."""
    if not area_path.exists():
        return []
    return sorted(
        str(p.relative_to(PROJECT_ROOT)) + "/"
        for p in area_path.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    )


def import_smoke_test() -> list[str]:
    """Imports each module in SMOKE_IMPORT_MODULES in its own
    subprocess (cwd=agent/, so both `backend.*` and the top-level
    `cli`/`server` resolve), so one bad import can't take down the
    rest. Reports failures only. Confirms importability, not runtime
    behavior."""
    failures = []
    for module in SMOKE_IMPORT_MODULES:
        code, output = _run([str(PYTHON), "-c", f"import {module}"])
        if code != 0:
            last_line = output.splitlines()[-1] if output else "failed, no output captured"
            failures.append(f"{module}: {last_line}")
    return failures


def run_tool(module: str) -> tuple[int, str]:
    """Run another script in this same tools/ package as a subprocess
    (docs_check.py, docs_lint.py)."""
    return _run([str(PYTHON), "-m", f"tools.{module}"], cwd=PROJECT_ROOT)


def run_pyflakes() -> tuple[int, str]:
    """Run pyflakes (see agent/requirements.txt) against agent/'s
    backend/ and its top-level entry points."""
    return _run([str(PYTHON), "-m", "pyflakes", "backend", "cli.py", "server.py"])


# A backend/...-looking .py path mentioned in a comment, docstring, or
# docs/ prose. No "frontend/" branch yet - see PY_SCAN_AREAS above.
CODE_PATH_RE = re.compile(r"\bbackend/[A-Za-z0-9_/().-]+\.py\b")

# Where to scan for CODE_PATH_RE mentions: .py under agent/backend/ and
# its top-level entry points, .md under the shared docs/.
STALE_PATH_SCAN_TARGETS: list[tuple[Path, str]] = [
    (AGENT_ROOT / "backend", "*.py"),
    (AGENT_ROOT, "cli.py"),
    (AGENT_ROOT, "server.py"),
    (DOCS_ROOT, "*.md"),
]


def stale_code_path_mentions() -> list[str]:
    """Every backend/...-looking .py path mentioned anywhere under
    agent/backend/, agent/cli.py, agent/server.py, or the shared docs/
    that doesn't resolve to a real file under agent/ (a docs/ mention
    of `backend/...` means agent/backend/... specifically -
    current/backend/ uses the same relative shape but a different tree
    entirely). Doesn't distinguish a genuine leftover reference from a
    docstring or doc deliberately narrating "moved from X" as
    history."""
    stale = []
    for area_path, pattern in STALE_PATH_SCAN_TARGETS:
        if not area_path.exists():
            continue
        paths = [area_path] if area_path.is_file() and area_path.match(pattern) else sorted(area_path.rglob(pattern))
        for path in paths:
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in CODE_PATH_RE.finditer(line):
                    referenced = match.group(0)
                    if not (AGENT_ROOT / referenced).exists():
                        stale.append(f"{path.relative_to(PROJECT_ROOT)}:{line_number}: {referenced}")
    return stale


def modules_with_no_inbound_import() -> list[str]:
    """Backend modules (excluding __init__.py) that no other .py file
    in PY_SCAN_AREAS/PY_SCAN_FILES appears to mention by dotted path or
    bare filename. A plain text search, not real import-graph analysis
    - many hits here are legitimate entry points (see
    SMOKE_IMPORT_MODULES) rather than dead code."""
    py_files = [
        p
        for area in PY_SCAN_AREAS
        for p in (AGENT_ROOT / area).rglob("*.py")
        if "__pycache__" not in p.parts
    ] + [AGENT_ROOT / f for f in PY_SCAN_FILES if (AGENT_ROOT / f).exists()]
    contents = {p: p.read_text(encoding="utf-8", errors="replace") for p in py_files}
    backend_modules = [
        p
        for p in (AGENT_ROOT / "backend").rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    ]

    orphans = []
    for module_path in backend_modules:
        dotted = ".".join(module_path.relative_to(AGENT_ROOT).with_suffix("").parts)
        base = module_path.stem
        referenced = any(
            dotted in text or f"import {base}" in text or f".{base}" in text
            for other_path, text in contents.items()
            if other_path != module_path
        )
        if not referenced:
            orphans.append(str(module_path.relative_to(AGENT_ROOT)))
    return sorted(orphans)


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
    print("=== agent/backend/ tree (compare against docs/04-current-state.md § 1. Project Structure) ===")
    for line in directory_tree(AGENT_ROOT / "backend"):
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
    print("=== pyflakes (agent/backend/, agent/cli.py, agent/server.py) ===")
    code, output = run_pyflakes()
    print(output if output else "  no issues found")
    if code != 0:
        exit_code = 1

    print()
    print("=== stale agent/backend/ .py path mentions ===")
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
    print("=== agent/backend/ modules with no detected inbound import ===")
    orphans = modules_with_no_inbound_import()
    if orphans:
        for path in orphans:
            print(f"  {path}")
        print()
        print("  (observed fact only - a module can legitimately have")
        print("  no inbound import because it's a command-line entry")
        print("  point (see SMOKE_IMPORT_MODULES above), or because it's")
        print("  built but deliberately not yet wired in - see")
        print("  docs/04-current-state.md § 5 for Module Library, the")
        print("  known example of the latter as of this writing; that")
        print("  judgment is not this script's.)")
    else:
        print("  none")

    print()
    print("=== docs_check.py ===")
    code, output = run_tool("docs_check")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    print()
    print("=== docs_lint.py ===")
    code, output = run_tool("docs_lint")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
