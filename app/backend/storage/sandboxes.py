"""
The public demo's sandboxes (docs/05-decisions.md #70,
docs/demo.md): one folder per visitor session,
holding a fresh copy of the demo seed.

While a request runs in demo mode, current() is that visitor's folder,
and the storage modules read and write there instead of data/.
Outside demo mode nothing calls use(), so current() is None and storage
uses data/ as always.

Each server thread answers one request at a time and backend/api/demo/
calls use() at the start of every demo request, so the value never
carries over to another visitor's request.
"""

# Contents
#  1. Settings
#      - SEED_DIR, ROOT
#
#  2. The current sandbox
#      - current(), use()
#
#  3. Making and removing sandboxes
#      - create(), remove(), clear_all()

import os
import re
import secrets
import shutil
import tempfile
from contextvars import ContextVar
from pathlib import Path


# ============================================================
# 1. Settings
# ============================================================

# app/demo_seed — what every new sandbox starts as. Never written to.
SEED_DIR = Path(__file__).resolve().parents[2] / "demo_seed"

# Kept out of app/data/ so a sandbox can never be mistaken for real data.
ROOT = Path(
    os.environ.get("DEMO_SANDBOX_DIR", "").strip()
    or Path(tempfile.gettempdir()) / "project1-demo-sandboxes"
)

# Sandbox folder names; nothing else under ROOT is ever deleted.
_ID = re.compile(r"^[0-9a-f]{16}$")

_current: ContextVar[Path | None] = ContextVar("sandbox", default=None)


# ============================================================
# 2. The current sandbox
# ============================================================

def current() -> Path | None:
    """The folder storage uses for this request, or None for data/."""
    return _current.get()


def use(sandbox_id: str | None) -> None:
    """Point this request's storage at `sandbox_id`'s folder (None:
    data/). Called first on every request in demo mode."""
    if sandbox_id is not None and not _ID.match(sandbox_id):
        raise ValueError("not a sandbox id")
    _current.set(ROOT / sandbox_id if sandbox_id else None)


# ============================================================
# 3. Making and removing sandboxes
# ============================================================

def create() -> str:
    """A new sandbox: a copy of SEED_DIR (empty if there is no seed).
    Returns its id."""
    sandbox_id = secrets.token_hex(8)
    ROOT.mkdir(parents=True, exist_ok=True)
    folder = ROOT / sandbox_id
    if SEED_DIR.is_dir():
        shutil.copytree(SEED_DIR, folder)
    else:
        folder.mkdir()
    return sandbox_id


def remove(sandbox_id: str | None) -> None:
    if sandbox_id and _ID.match(sandbox_id):
        shutil.rmtree(ROOT / sandbox_id, ignore_errors=True)


def clear_all() -> None:
    """Remove every sandbox: at start no session exists, so none is in
    use. Only folders named like a sandbox are touched."""
    if not ROOT.is_dir():
        return
    for child in ROOT.iterdir():
        if child.is_dir() and _ID.match(child.name):
            shutil.rmtree(child, ignore_errors=True)
