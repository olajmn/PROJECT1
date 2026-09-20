"""
Small, direct checks for simulated-user / Session persistence and
plans.jsonl (including one-shot migration from a legacy plans.json
array, and vision_id → sim_user_id / visions.json → users.json).

Runs entirely against a temporary directory, never the real data/ -
this module patches DATA_DIR / PLANS_FILE / LEGACY_PLANS_FILE /
USERS_FILE / LEGACY_VISIONS_FILE on data_persistence and SESSIONS_FILE
on session for the duration of the run and restores them afterward.

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
_original_users_file = dp.USERS_FILE
_original_legacy_visions = dp.LEGACY_VISIONS_FILE
_original_sessions_file = session_store.SESSIONS_FILE

_tmp_dir = Path(tempfile.mkdtemp(prefix="data_persistence_test_"))
dp.DATA_DIR = _tmp_dir
dp.PLANS_FILE = _tmp_dir / "plans.jsonl"
dp.LEGACY_PLANS_FILE = _tmp_dir / "plans.json"
dp.USERS_FILE = _tmp_dir / "users.json"
dp.LEGACY_VISIONS_FILE = _tmp_dir / "visions.json"
session_store.SESSIONS_FILE = _tmp_dir / "sessions.json"

try:
    # A goal saved with no sim_user_id at all - the normal case - must
    # come back with sim_user_id present and None, not simply missing,
    # so every reader can rely on the key existing.
    plain_record = dp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["sim_user_id"] is None, plain_record["sim_user_id"]
    assert dp.PLANS_FILE.exists()
    assert dp.PLANS_FILE.read_text(encoding="utf-8").count("\n") == 1

    # Creating a simulated user mints an id and is readable back by it.
    user = dp.save_user("Improve physical health and quality of life")
    assert user["text"] == "Improve physical health and quality of life"
    assert dp.get_user(user["id"]) == user
    assert dp.get_user(user["id"] + 999) is None  # unknown id - never guessed, just None

    # A second user gets the next id, not a collision.
    second_user = dp.save_user("Grow as a musician")
    assert second_user["id"] == user["id"] + 1
    assert [u["id"] for u in dp.load_users()] == [user["id"], second_user["id"]]

    # Two independent goals can share one sim_user_id.
    abs_goal = dp.save_plan("Get visible abs", {"now": "..."}, sim_user_id=user["id"])
    cardio_goal = dp.save_plan("Improve cardio", {"now": "..."}, sim_user_id=user["id"])
    assert abs_goal["sim_user_id"] == cardio_goal["sim_user_id"] == user["id"]
    assert abs_goal["project_id"] != cardio_goal["project_id"]
    assert "goal_id" not in abs_goal
    assert "vision_id" not in abs_goal
    assert len(dp.load_history()) == 3

    print("OK - user / plans.jsonl persistence behaves as expected")

    # A new Session mints an id and starts with no end time.
    first_session = session_store.start_session()
    assert first_session["id"] == 1
    assert first_session["ended_at"] is None
    assert first_session["started_at"]

    # A second Session gets the next id, not a collision - same
    # minting idiom as project_id/sim_user_id above.
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
    assert history[0]["sim_user_id"] is None
    assert "goal_id" not in history[0]
    assert "vision_id" not in history[0]
    assert dp.PLANS_FILE.exists()
    assert not dp.LEGACY_PLANS_FILE.exists()
    assert dp.LEGACY_PLANS_FILE.with_suffix(".json.bak").exists()
    disk_line = dp.PLANS_FILE.read_text(encoding="utf-8").strip()
    assert '"project_id"' in disk_line
    assert '"goal_id"' not in disk_line
    assert '"sim_user_id"' in disk_line
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

    # Existing plans.jsonl with vision_id is rewritten to sim_user_id.
    vision_promote_dir = Path(tempfile.mkdtemp(prefix="vision_promote_test_"))
    dp.DATA_DIR = vision_promote_dir
    dp.PLANS_FILE = vision_promote_dir / "plans.jsonl"
    dp.LEGACY_PLANS_FILE = vision_promote_dir / "plans.json"
    dp.USERS_FILE = vision_promote_dir / "users.json"
    dp.LEGACY_VISIONS_FILE = vision_promote_dir / "visions.json"
    dp.PLANS_FILE.write_text(
        json.dumps({
            "id": 1,
            "project_id": 3,
            "user_id": 1,
            "vision_id": 2,
            "goal": "Had a vision",
            "plan": {"now": "x"},
            "created_at": "2026-01-01T00:00:00",
        }, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    vpromoted = dp.load_history()
    assert vpromoted[0]["sim_user_id"] == 2
    assert "vision_id" not in vpromoted[0]
    vdisk = dp.PLANS_FILE.read_text(encoding="utf-8")
    assert '"sim_user_id": 2' in vdisk
    assert "vision_id" not in vdisk
    shutil.rmtree(vision_promote_dir, ignore_errors=True)

    print("OK - vision_id → sim_user_id JSONL promotion behaves as expected")

    # Legacy visions.json is promoted to users.json on first load.
    visions_migrate_dir = Path(tempfile.mkdtemp(prefix="visions_migrate_test_"))
    dp.DATA_DIR = visions_migrate_dir
    dp.USERS_FILE = visions_migrate_dir / "users.json"
    dp.LEGACY_VISIONS_FILE = visions_migrate_dir / "visions.json"
    dp.LEGACY_VISIONS_FILE.write_text(
        json.dumps([
            {
                "id": 1,
                "user_id": 1,
                "text": "Legacy vision text",
                "created_at": "2026-01-01T00:00:00",
            },
        ], indent=2),
        encoding="utf-8",
    )
    loaded = dp.load_users()
    assert len(loaded) == 1
    assert loaded[0]["text"] == "Legacy vision text"
    assert dp.USERS_FILE.exists()
    assert json.loads(dp.USERS_FILE.read_text(encoding="utf-8"))[0]["id"] == 1
    shutil.rmtree(visions_migrate_dir, ignore_errors=True)

    print("OK - visions.json → users.json promote behaves as expected")
finally:
    dp.DATA_DIR = _original_data_dir
    dp.PLANS_FILE = _original_plans_file
    dp.LEGACY_PLANS_FILE = _original_legacy_plans
    dp.USERS_FILE = _original_users_file
    dp.LEGACY_VISIONS_FILE = _original_legacy_visions
    session_store.SESSIONS_FILE = _original_sessions_file
    shutil.rmtree(_tmp_dir, ignore_errors=True)
