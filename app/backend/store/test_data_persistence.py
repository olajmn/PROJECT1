"""
Small, direct checks for Vision / Session persistence and plans.jsonl
(including one-shot migration from a legacy plans.json array).

Runs entirely against a temporary directory, never the real data/ -
this module patches DATA_DIR / PLANS_FILE / LEGACY_PLANS_FILE /
VISIONS_FILE on data_persistence and SESSIONS_FILE on session for the
duration of the run and restores them afterward.

Run from app/:
    .venv/bin/python -m backend.store.test_data_persistence
"""

import json
import shutil
import tempfile
from pathlib import Path

from backend.store import data_persistence as dp
from backend.store import session as session_store

_original_data_dir = dp.DATA_DIR
_original_plans_file = dp.PLANS_FILE
_original_legacy_plans = dp.LEGACY_PLANS_FILE
_original_visions_file = dp.VISIONS_FILE
_original_sessions_file = session_store.SESSIONS_FILE

_tmp_dir = Path(tempfile.mkdtemp(prefix="data_persistence_test_"))
dp.DATA_DIR = _tmp_dir
dp.PLANS_FILE = _tmp_dir / "plans.jsonl"
dp.LEGACY_PLANS_FILE = _tmp_dir / "plans.json"
dp.VISIONS_FILE = _tmp_dir / "visions.json"
session_store.SESSIONS_FILE = _tmp_dir / "sessions.json"

try:
    # A goal saved with no vision_id at all - the normal case - must
    # come back with vision_id present and None, not simply missing,
    # so every reader can rely on the key existing.
    plain_record = dp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["vision_id"] is None, plain_record["vision_id"]
    assert dp.PLANS_FILE.exists()
    assert dp.PLANS_FILE.read_text(encoding="utf-8").count("\n") == 1

    # Creating a Vision mints an id and is readable back by it.
    vision = dp.save_vision("Improve physical health and quality of life")
    assert vision["text"] == "Improve physical health and quality of life"
    assert dp.get_vision(vision["id"]) == vision
    assert dp.get_vision(vision["id"] + 999) is None  # unknown id - never guessed, just None

    # A second Vision gets the next id, not a collision.
    second_vision = dp.save_vision("Grow as a musician")
    assert second_vision["id"] == vision["id"] + 1
    assert [v["id"] for v in dp.load_visions()] == [vision["id"], second_vision["id"]]

    # Two independent goals can share one vision_id - the actual point
    # of Vision: it isn't copied text, it's a shared reference.
    abs_goal = dp.save_plan("Get visible abs", {"now": "..."}, vision_id=vision["id"])
    cardio_goal = dp.save_plan("Improve cardio", {"now": "..."}, vision_id=vision["id"])
    assert abs_goal["vision_id"] == cardio_goal["vision_id"] == vision["id"]
    assert abs_goal["project_id"] != cardio_goal["project_id"]
    assert "goal_id" not in abs_goal
    assert len(dp.load_history()) == 3

    print("OK - vision / plans.jsonl persistence behaves as expected")

    # A new Session mints an id and starts with no end time.
    first_session = session_store.start_session()
    assert first_session["id"] == 1
    assert first_session["ended_at"] is None
    assert first_session["started_at"]

    # A second Session gets the next id, not a collision - same
    # minting idiom as project_id/vision_id above.
    second_session = session_store.start_session()
    assert second_session["id"] == first_session["id"] + 1
    assert [s["id"] for s in session_store.load_sessions()] == [
        first_session["id"], second_session["id"],
    ]

    print("OK - session persistence behaves as expected")

    # Legacy plans.json array migrates to plans.jsonl once.
    migrate_dir = Path(tempfile.mkdtemp(prefix="plans_migrate_test_"))
    dp.DATA_DIR = migrate_dir
    dp.PLANS_FILE = migrate_dir / "plans.jsonl"
    dp.LEGACY_PLANS_FILE = migrate_dir / "plans.json"
    legacy = [
        {
            "id": 1,
            "goal_id": 1,
            "user_id": 1,
            "goal": "Legacy goal",
            "plan": {"now": "Do the thing"},
            "created_at": "2026-01-01T00:00:00",
        },
    ]
    dp.LEGACY_PLANS_FILE.write_text(
        json.dumps(legacy, indent=2), encoding="utf-8",
    )
    history = dp.load_history()
    assert len(history) == 1
    assert history[0]["goal"] == "Legacy goal"
    assert history[0]["project_id"] == 1
    assert "goal_id" not in history[0]
    assert dp.PLANS_FILE.exists()
    assert not dp.LEGACY_PLANS_FILE.exists()
    assert dp.LEGACY_PLANS_FILE.with_suffix(".json.bak").exists()
    disk_line = dp.PLANS_FILE.read_text(encoding="utf-8").strip()
    assert '"project_id"' in disk_line
    assert '"goal_id"' not in disk_line
    shutil.rmtree(migrate_dir, ignore_errors=True)

    print("OK - plans.json → plans.jsonl migration behaves as expected")

    # Existing plans.jsonl with goal_id only is rewritten to project_id.
    promote_dir = Path(tempfile.mkdtemp(prefix="plans_promote_test_"))
    dp.DATA_DIR = promote_dir
    dp.PLANS_FILE = promote_dir / "plans.jsonl"
    dp.LEGACY_PLANS_FILE = promote_dir / "plans.json"
    dp.PLANS_FILE.write_text(
        json.dumps({
            "id": 1,
            "goal_id": 7,
            "user_id": 1,
            "goal": "Promote me",
            "plan": {"now": "x"},
            "created_at": "2026-01-01T00:00:00",
        }, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    promoted = dp.load_history()
    assert promoted[0]["project_id"] == 7
    assert "goal_id" not in promoted[0]
    disk = dp.PLANS_FILE.read_text(encoding="utf-8")
    assert '"project_id": 7' in disk
    assert "goal_id" not in disk
    shutil.rmtree(promote_dir, ignore_errors=True)

    print("OK - goal_id → project_id JSONL promotion behaves as expected")
finally:
    dp.DATA_DIR = _original_data_dir
    dp.PLANS_FILE = _original_plans_file
    dp.LEGACY_PLANS_FILE = _original_legacy_plans
    dp.VISIONS_FILE = _original_visions_file
    session_store.SESSIONS_FILE = _original_sessions_file
    shutil.rmtree(_tmp_dir, ignore_errors=True)
