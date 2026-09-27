"""
Saved trees — data/saved_trees.json.

A per-account library of structures (see project/saved_trees/). Plain
records, no history: {id, name, account_id, saved_at, source, tree}.

Tree ids (`t1`, `t2`, …) are never reused: the file keeps an `id_hi`
high-water mark, as project plans keep `node_id_hi` for node ids, so a
deleted tree's id stays retired.
"""

# Contents
#  1. File
#      - _load() / _save()
#  2. Records
#      - add_saved_tree() / load_saved_trees() / get_saved_tree()
#      - delete_saved_tree()

import json

from backend.storage.paths import DATA_DIR, ensure_data_dir, now_utc

SAVED_TREES_FILE = DATA_DIR / "saved_trees.json"


# ============================================================
# 1. File
# ============================================================


def _load() -> dict:
    """{"id_hi": int, "trees": [...]}; empty library if no file yet."""
    if not SAVED_TREES_FILE.exists():
        return {"id_hi": 0, "trees": []}
    try:
        with open(SAVED_TREES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{SAVED_TREES_FILE} is corrupted and can't be read as JSON "
            f"({e}). It may have been interrupted mid-write. Restore it "
            "from a backup or fix it by hand before continuing."
        ) from e
    data.setdefault("id_hi", 0)
    data.setdefault("trees", [])
    return data


def _save(data: dict) -> None:
    """Write the whole library — atomic temp-file rename."""
    ensure_data_dir()
    tmp_file = SAVED_TREES_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_file.replace(SAVED_TREES_FILE)


# ============================================================
# 2. Records
# ============================================================


def add_saved_tree(
    name: str,
    tree: dict,
    account_id: int | None,
    source: dict | None = None,
) -> dict:
    """Store one structure and return its record. `source` records
    where it was saved from ({project_id, step_id}); nothing links
    back to it."""
    data = _load()
    data["id_hi"] += 1
    record = {
        "id": f"t{data['id_hi']}",
        "name": name,
        "account_id": account_id,
        "saved_at": now_utc(),
        "source": source or {},
        "tree": tree,
    }
    data["trees"].append(record)
    _save(data)
    return record


def load_saved_trees() -> list[dict]:
    """Every saved tree, oldest first."""
    return _load()["trees"]


def get_saved_tree(tree_id: str) -> dict | None:
    return next((t for t in load_saved_trees() if t["id"] == tree_id), None)


def delete_saved_tree(tree_id: str) -> dict | None:
    """Remove one tree; returns it, or None if missing. `id_hi` is
    untouched, so the id is not handed out again."""
    data = _load()
    for i, tree in enumerate(data["trees"]):
        if tree["id"] == tree_id:
            del data["trees"][i]
            _save(data)
            return tree
    return None
