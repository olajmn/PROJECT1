"""
Small, direct checks for simulated-user persistence and
per-project JSONL under data/projects/{id}.jsonl (including one-shot
split from a combined projects.jsonl / plans.jsonl / plans.json, and
vision_id → sim_user_id / visions.json → users.json).

Runs entirely against a temporary directory, never the real data/ -
this module patches DATA_DIR / PROJECTS_DIR / LEGACY_* / USERS_FILE on
data_persistence for the duration of the run and restores them
afterward.

Run from app/:
    .venv/bin/python -m backend.store.test_data_persistence
"""

import json
import shutil
import tempfile
from pathlib import Path

from backend.store import data_persistence as dp

_original_data_dir = dp.DATA_DIR
_original_projects_dir = dp.PROJECTS_DIR
_original_legacy_projects = dp.LEGACY_PROJECTS_JSONL
_original_legacy_plans_jsonl = dp.LEGACY_PLANS_JSONL
_original_legacy_plans = dp.LEGACY_PLANS_FILE
_original_users_file = dp.USERS_FILE
_original_legacy_visions = dp.LEGACY_VISIONS_FILE


def _point_at(root: Path) -> None:
    dp.DATA_DIR = root
    dp.PROJECTS_DIR = root / "projects"
    dp.LEGACY_PROJECTS_JSONL = root / "projects.jsonl"
    dp.LEGACY_PLANS_JSONL = root / "plans.jsonl"
    dp.LEGACY_PLANS_FILE = root / "plans.json"
    dp.USERS_FILE = root / "users.json"
    dp.LEGACY_VISIONS_FILE = root / "visions.json"


_tmp_dir = Path(tempfile.mkdtemp(prefix="data_persistence_test_"))
_point_at(_tmp_dir)

try:
    # A goal saved with no sim_user_id at all - the normal case - must
    # come back with sim_user_id present and None, not simply missing,
    # so every reader can rely on the key existing.
    plain_record = dp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["sim_user_id"] is None, plain_record["sim_user_id"]
    assert plain_record["name"] == "Make a song"
    assert "goal" not in plain_record
    assert plain_record["project_id"] == 1
    path_1 = dp.project_path(1)
    assert path_1.exists()
    assert path_1.read_text(encoding="utf-8").count("\n") == 1

    # Creating a simulated user mints an id and is readable back by it.
    user = dp.save_user("Improve physical health and quality of life")
    assert user["text"] == "Improve physical health and quality of life"
    assert dp.get_user(user["id"]) == user
    assert dp.get_user(user["id"] + 999) is None  # unknown id - never guessed, just None

    # A second user gets the next id, not a collision.
    second_user = dp.save_user("Grow as a musician")
    assert second_user["id"] == user["id"] + 1
    assert [u["id"] for u in dp.load_users()] == [user["id"], second_user["id"]]

    # Two independent goals get two files; append grows only the right one.
    abs_goal = dp.save_plan("Get visible abs", {"now": "..."}, sim_user_id=user["id"])
    cardio_goal = dp.save_plan("Improve cardio", {"now": "..."}, sim_user_id=user["id"])
    assert abs_goal["sim_user_id"] == cardio_goal["sim_user_id"] == user["id"]
    assert abs_goal["project_id"] != cardio_goal["project_id"]
    assert "goal_id" not in abs_goal
    assert "name" in abs_goal
    assert "goal" not in abs_goal
    assert "vision_id" not in abs_goal
    assert dp.project_path(abs_goal["project_id"]).exists()
    assert dp.project_path(cardio_goal["project_id"]).exists()
    assert len(dp.load_history()) == 3
    assert len(dp.load_project_history(abs_goal["project_id"])) == 1

    dp.save_plan(
        "Get visible abs",
        {"now": "again"},
        project_id=abs_goal["project_id"],
        sim_user_id=user["id"],
        event="chat",
    )
    assert dp.project_path(abs_goal["project_id"]).read_text(encoding="utf-8").count("\n") == 2
    assert dp.project_path(cardio_goal["project_id"]).read_text(encoding="utf-8").count("\n") == 1

    print("OK - user / per-project JSONL persistence behaves as expected")

    # Legacy plans.json array splits into projects/{id}.jsonl once.
    migrate_dir = Path(tempfile.mkdtemp(prefix="plans_migrate_test_"))
    _point_at(migrate_dir)
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
    assert history[0]["name"] == "Legacy goal"
    assert history[0]["project_id"] == 1
    assert history[0]["sim_user_id"] is None
    assert "goal_id" not in history[0]
    assert "vision_id" not in history[0]
    assert dp.project_path(1).exists()
    assert not dp.LEGACY_PLANS_FILE.exists()
    assert dp._bak_path(dp.LEGACY_PLANS_FILE).exists()
    disk_line = dp.project_path(1).read_text(encoding="utf-8").strip()
    assert '"project_id"' in disk_line
    assert '"goal_id"' not in disk_line
    assert '"name"' in disk_line
    assert '"goal"' not in disk_line
    assert '"sim_user_id"' in disk_line
    shutil.rmtree(migrate_dir, ignore_errors=True)

    print("OK - plans.json → projects/{id}.jsonl migration behaves as expected")

    # Combined projects.jsonl splits into per-project files.
    split_dir = Path(tempfile.mkdtemp(prefix="projects_split_test_"))
    _point_at(split_dir)
    lines = [
        {
            "id": 1,
            "project_id": 4,
            "user_id": 1,
            "goal": "Alpha",
            "plan": {"now": "x"},
            "created_at": "2026-01-01T00:00:00",
            "sim_user_id": None,
        },
        {
            "id": 2,
            "project_id": 7,
            "user_id": 1,
            "goal": "Beta",
            "plan": {"now": "y"},
            "created_at": "2026-01-02T00:00:00",
            "sim_user_id": None,
        },
        {
            "id": 3,
            "project_id": 4,
            "user_id": 1,
            "goal": "Alpha",
            "plan": {"now": "z"},
            "created_at": "2026-01-03T00:00:00",
            "sim_user_id": None,
        },
    ]
    dp.LEGACY_PROJECTS_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lines),
        encoding="utf-8",
    )
    split = dp.load_history()
    assert len(split) == 3
    assert len(dp.load_project_history(4)) == 2
    assert len(dp.load_project_history(7)) == 1
    assert dp.project_path(4).exists()
    assert dp.project_path(7).exists()
    assert not dp.LEGACY_PROJECTS_JSONL.exists()
    assert dp._bak_path(dp.LEGACY_PROJECTS_JSONL).exists()
    shutil.rmtree(split_dir, ignore_errors=True)

    print("OK - projects.jsonl → projects/{id}.jsonl split behaves as expected")

    # Leftover plans.jsonl also splits (same path as combined projects.jsonl).
    rename_dir = Path(tempfile.mkdtemp(prefix="plans_jsonl_split_test_"))
    _point_at(rename_dir)
    dp.LEGACY_PLANS_JSONL.write_text(
        json.dumps({
            "id": 1,
            "project_id": 4,
            "user_id": 1,
            "goal": "Rename me",
            "plan": {"now": "x"},
            "created_at": "2026-01-01T00:00:00",
            "sim_user_id": None,
        }, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    renamed = dp.load_history()
    assert renamed[0]["project_id"] == 4
    assert dp.project_path(4).exists()
    assert not dp.LEGACY_PLANS_JSONL.exists()
    assert dp._bak_path(dp.LEGACY_PLANS_JSONL).exists()
    shutil.rmtree(rename_dir, ignore_errors=True)

    print("OK - plans.jsonl → projects/{id}.jsonl split behaves as expected")

    # Existing project file with goal_id only is rewritten to project_id.
    promote_dir = Path(tempfile.mkdtemp(prefix="plans_promote_test_"))
    _point_at(promote_dir)
    dp._ensure_projects_dir()
    dp.project_path(7).write_text(
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
    promoted = dp.load_project_history(7)
    assert promoted[0]["project_id"] == 7
    assert promoted[0]["name"] == "Promote me"
    assert "goal_id" not in promoted[0]
    assert "goal" not in promoted[0]
    disk = dp.project_path(7).read_text(encoding="utf-8")
    assert '"project_id": 7' in disk
    assert "goal_id" not in disk
    assert '"name"' in disk
    assert '"goal"' not in disk
    shutil.rmtree(promote_dir, ignore_errors=True)

    print("OK - goal_id → project_id and goal → name JSONL promotion behaves as expected")

    # Existing project file with vision_id is rewritten to sim_user_id.
    vision_promote_dir = Path(tempfile.mkdtemp(prefix="vision_promote_test_"))
    _point_at(vision_promote_dir)
    dp._ensure_projects_dir()
    dp.project_path(3).write_text(
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
    vpromoted = dp.load_project_history(3)
    assert vpromoted[0]["sim_user_id"] == 2
    assert vpromoted[0]["name"] == "Had a vision"
    assert "goal" not in vpromoted[0]
    assert "vision_id" not in vpromoted[0]
    vdisk = dp.project_path(3).read_text(encoding="utf-8")
    assert '"sim_user_id": 2' in vdisk
    assert "vision_id" not in vdisk
    shutil.rmtree(vision_promote_dir, ignore_errors=True)

    print("OK - vision_id → sim_user_id JSONL promotion behaves as expected")

    # Legacy visions.json is promoted to users.json on first load.
    visions_migrate_dir = Path(tempfile.mkdtemp(prefix="visions_migrate_test_"))
    _point_at(visions_migrate_dir)
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
    dp.PROJECTS_DIR = _original_projects_dir
    dp.LEGACY_PROJECTS_JSONL = _original_legacy_projects
    dp.LEGACY_PLANS_JSONL = _original_legacy_plans_jsonl
    dp.LEGACY_PLANS_FILE = _original_legacy_plans
    dp.USERS_FILE = _original_users_file
    dp.LEGACY_VISIONS_FILE = _original_legacy_visions
    shutil.rmtree(_tmp_dir, ignore_errors=True)
