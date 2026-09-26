"""
Small, direct checks for simulated-user persistence and
per-project current.json + events.jsonl under data/projects/{id}/
(including one-shot split from a combined projects.jsonl / plans.jsonl /
plans.json, snapshot {id}.jsonl → folder, and vision_id → sim_user_id /
visions.json → users.json).

Runs entirely against a temporary directory, never the real data/ -
this module patches path constants on project_persistence /
users_persistence / paths for the duration of the run and restores them
afterward.

Run from app/:
    .venv/bin/python -m backend.storage.test_storage
"""

import json
import shutil
import tempfile
from pathlib import Path

from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp
from backend.storage import users_persistence as up

_original_paths_data_dir = storage_paths.DATA_DIR
_original_pp = {
    "DATA_DIR": pp.DATA_DIR,
    "PROJECTS_DIR": pp.PROJECTS_DIR,
    "LEGACY_PROJECTS_JSONL": pp.LEGACY_PROJECTS_JSONL,
    "LEGACY_PLANS_JSONL": pp.LEGACY_PLANS_JSONL,
    "LEGACY_PLANS_FILE": pp.LEGACY_PLANS_FILE,
}
_original_up = {
    "USERS_FILE": up.USERS_FILE,
    "LEGACY_VISIONS_FILE": up.LEGACY_VISIONS_FILE,
}


def _point_at(root: Path) -> None:
    storage_paths.DATA_DIR = root
    pp.DATA_DIR = root
    pp.PROJECTS_DIR = root / "projects"
    pp.LEGACY_PROJECTS_JSONL = root / "projects.jsonl"
    pp.LEGACY_PLANS_JSONL = root / "plans.jsonl"
    pp.LEGACY_PLANS_FILE = root / "plans.json"
    up.USERS_FILE = root / "users.json"
    up.LEGACY_VISIONS_FILE = root / "visions.json"


_tmp_dir = Path(tempfile.mkdtemp(prefix="store_test_"))
_point_at(_tmp_dir)

try:
    plain_record = pp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["sim_user_id"] is None, plain_record["sim_user_id"]
    assert plain_record["name"] == "Make a song"
    assert "goal" not in plain_record
    assert plain_record["project_id"] == 1
    assert pp.current_path(1).exists()
    assert pp.events_path(1).exists()
    assert "plan" in pp.load_current(1)
    assert "plan" not in pp.load_project_events(1)[0]
    assert pp.events_path(1).read_text(encoding="utf-8").count("\n") == 1

    user = up.save_user("Improve physical health and quality of life")
    assert user["text"] == "Improve physical health and quality of life"
    assert up.get_user(user["id"]) == user
    assert up.get_user(user["id"] + 999) is None

    second_user = up.save_user("Grow as a musician")
    assert second_user["id"] == user["id"] + 1
    assert [u["id"] for u in up.load_users()] == [user["id"], second_user["id"]]

    abs_goal = pp.save_plan("Get visible abs", {"now": "..."}, sim_user_id=user["id"])
    cardio_goal = pp.save_plan("Improve cardio", {"now": "..."}, sim_user_id=user["id"])
    assert abs_goal["sim_user_id"] == cardio_goal["sim_user_id"] == user["id"]
    assert abs_goal["project_id"] != cardio_goal["project_id"]
    assert "goal_id" not in abs_goal
    assert "name" in abs_goal
    assert "goal" not in abs_goal
    assert "vision_id" not in abs_goal
    assert pp.current_path(abs_goal["project_id"]).exists()
    assert pp.current_path(cardio_goal["project_id"]).exists()
    assert len(pp.load_history()) == 3
    assert len(pp.load_project_history(abs_goal["project_id"])) == 1

    pp.save_plan(
        "Get visible abs",
        {"now": "again"},
        project_id=abs_goal["project_id"],
        sim_user_id=user["id"],
        event="chat",
    )
    assert pp.events_path(abs_goal["project_id"]).read_text(encoding="utf-8").count("\n") == 2
    assert pp.events_path(cardio_goal["project_id"]).read_text(encoding="utf-8").count("\n") == 1
    assert pp.load_current(abs_goal["project_id"])["plan"]["now"] == "again"

    print("OK - user / current+events persistence behaves as expected")

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
    pp.LEGACY_PLANS_FILE.write_text(
        json.dumps(legacy, indent=2), encoding="utf-8",
    )
    history = pp.load_history()
    assert len(history) == 1
    assert history[0]["name"] == "Legacy goal"
    assert "plan" not in history[0]
    current = pp.load_current(1)
    assert current["name"] == "Legacy goal"
    assert current["project_id"] == 1
    assert current["sim_user_id"] is None
    assert "goal_id" not in current
    assert "vision_id" not in current
    assert pp.current_path(1).exists()
    assert not pp.LEGACY_PLANS_FILE.exists()
    assert pp._bak_path(pp.LEGACY_PLANS_FILE).exists()
    disk = pp.current_path(1).read_text(encoding="utf-8")
    assert '"project_id"' in disk
    assert '"goal_id"' not in disk
    assert '"name"' in disk
    assert '"goal"' not in disk
    assert '"sim_user_id"' in disk
    shutil.rmtree(migrate_dir, ignore_errors=True)

    print("OK - plans.json → projects/{id}/current+events migration behaves as expected")

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
    pp.LEGACY_PROJECTS_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lines),
        encoding="utf-8",
    )
    split = pp.load_history()
    assert len(split) == 3
    assert len(pp.load_project_history(4)) == 2
    assert len(pp.load_project_history(7)) == 1
    assert pp.load_current(4)["plan"]["now"] == "z"
    assert pp.current_path(4).exists()
    assert pp.current_path(7).exists()
    assert not pp.LEGACY_PROJECTS_JSONL.exists()
    assert pp._bak_path(pp.LEGACY_PROJECTS_JSONL).exists()
    shutil.rmtree(split_dir, ignore_errors=True)

    print("OK - projects.jsonl → projects/{id}/current+events split behaves as expected")

    rename_dir = Path(tempfile.mkdtemp(prefix="plans_jsonl_split_test_"))
    _point_at(rename_dir)
    pp.LEGACY_PLANS_JSONL.write_text(
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
    renamed = pp.load_history()
    assert renamed[0]["project_id"] == 4
    assert pp.current_path(4).exists()
    assert not pp.LEGACY_PLANS_JSONL.exists()
    assert pp._bak_path(pp.LEGACY_PLANS_JSONL).exists()
    shutil.rmtree(rename_dir, ignore_errors=True)

    print("OK - plans.jsonl → projects/{id}/current+events split behaves as expected")

    snap_dir = Path(tempfile.mkdtemp(prefix="snapshot_promote_test_"))
    _point_at(snap_dir)
    pp._ensure_projects_dir()
    pp._legacy_snapshot_path(7).write_text(
        json.dumps({
            "id": 1,
            "goal_id": 7,
            "user_id": 1,
            "goal": "Promote me",
            "plan": {"now": "x", "progression": {"steps": [{"label": "A"}]}},
            "created_at": "2026-01-01T00:00:00",
        }, ensure_ascii=False) + "\n"
        + json.dumps({
            "id": 2,
            "goal_id": 7,
            "user_id": 1,
            "goal": "Promote me",
            "plan": {"now": "y", "progression": {"steps": [{"label": "A"}, {"label": "B"}]}},
            "feedback": "Added step: B",
            "event": "node_added",
            "created_at": "2026-01-02T00:00:00",
        }, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    promoted = pp.load_project_history(7)
    assert len(promoted) == 2
    assert "plan" not in promoted[0]
    assert promoted[1].get("event") == "node_added"
    assert "surface" in promoted[1]
    current = pp.load_current(7)
    assert current["project_id"] == 7
    assert current["name"] == "Promote me"
    assert current["plan"]["now"] == "y"
    assert "goal_id" not in current
    assert "goal" not in current
    assert pp.current_path(7).exists()
    assert pp.events_path(7).exists()
    assert not pp._legacy_snapshot_path(7).exists()
    assert pp._bak_path(pp._legacy_snapshot_path(7)).exists()
    shutil.rmtree(snap_dir, ignore_errors=True)

    print("OK - {id}.jsonl → current+events promotion behaves as expected")

    vision_promote_dir = Path(tempfile.mkdtemp(prefix="vision_promote_test_"))
    _point_at(vision_promote_dir)
    pp._ensure_projects_dir()
    pp._legacy_snapshot_path(3).write_text(
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
    vpromoted = pp.load_current(3)
    assert vpromoted["sim_user_id"] == 2
    assert vpromoted["name"] == "Had a vision"
    assert "goal" not in vpromoted
    assert "vision_id" not in vpromoted
    vdisk = pp.current_path(3).read_text(encoding="utf-8")
    assert '"sim_user_id": 2' in vdisk
    assert "vision_id" not in vdisk
    shutil.rmtree(vision_promote_dir, ignore_errors=True)

    print("OK - vision_id → sim_user_id on current promote behaves as expected")

    visions_migrate_dir = Path(tempfile.mkdtemp(prefix="visions_migrate_test_"))
    _point_at(visions_migrate_dir)
    up.LEGACY_VISIONS_FILE.write_text(
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
    loaded = up.load_users()
    assert len(loaded) == 1
    assert loaded[0]["text"] == "Legacy vision text"
    assert up.USERS_FILE.exists()
    assert json.loads(up.USERS_FILE.read_text(encoding="utf-8"))[0]["id"] == 1
    shutil.rmtree(visions_migrate_dir, ignore_errors=True)

    print("OK - visions.json → users.json promote behaves as expected")
finally:
    storage_paths.DATA_DIR = _original_paths_data_dir
    for key, value in _original_pp.items():
        setattr(pp, key, value)
    for key, value in _original_up.items():
        setattr(up, key, value)
    shutil.rmtree(_tmp_dir, ignore_errors=True)
