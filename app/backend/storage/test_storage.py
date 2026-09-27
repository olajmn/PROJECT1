"""
Small, direct checks for account persistence and per-project
current.json + events.jsonl under data/projects/{id}/, plus
create_project()'s default `New project N` naming, since it only reads
what storage holds.

Runs entirely against a temporary directory, never the real data/ -
this module patches path constants on project_persistence /
accounts_persistence / paths for the duration of the run and restores
them afterward.

Run from app/:
    .venv/bin/python -m backend.storage.test_storage
"""

import shutil
import tempfile
from pathlib import Path

from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp
from backend.storage import accounts_persistence as ap

_original_paths_data_dir = storage_paths.DATA_DIR
_original_pp = {
    "DATA_DIR": pp.DATA_DIR,
    "PROJECTS_DIR": pp.PROJECTS_DIR,
}
_original_ap = {
    "ACCOUNTS_FILE": ap.ACCOUNTS_FILE,
}


def _point_at(root: Path) -> None:
    storage_paths.DATA_DIR = root
    pp.DATA_DIR = root
    pp.PROJECTS_DIR = root / "projects"
    ap.ACCOUNTS_FILE = root / "accounts.json"


_tmp_dir = Path(tempfile.mkdtemp(prefix="store_test_"))
_point_at(_tmp_dir)

try:
    plain_record = pp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["account_id"] is None, plain_record["account_id"]
    assert plain_record["name"] == "Make a song"
    assert "goal" not in plain_record
    assert plain_record["project_id"] == 1
    assert pp.current_path(1).exists()
    assert pp.events_path(1).exists()
    assert "plan" in pp.load_current(1)
    assert "plan" not in pp.load_project_events(1)[0]
    assert pp.events_path(1).read_text(encoding="utf-8").count("\n") == 1

    user = ap.save_account("Improve physical health and quality of life")
    assert user["text"] == "Improve physical health and quality of life"
    assert ap.get_account(user["id"]) == user
    assert ap.get_account(user["id"] + 999) is None
    renamed = ap.rename_account(user["id"], "Health")
    assert renamed is not None and renamed["text"] == "Health"
    assert ap.rename_account(user["id"], "  ")["text"] == "user"

    second_user = ap.save_account("Grow as a musician")
    assert second_user["id"] == user["id"] + 1
    assert [u["id"] for u in ap.load_accounts()] == [user["id"], second_user["id"]]

    abs_project = pp.save_plan("Get visible abs", {"now": "..."}, account_id=user["id"])
    cardio_project = pp.save_plan("Improve cardio", {"now": "..."}, account_id=user["id"])
    assert abs_project["account_id"] == cardio_project["account_id"] == user["id"]
    assert abs_project["project_id"] != cardio_project["project_id"]
    assert abs_project["account_n"] == 1
    assert cardio_project["account_n"] == 2
    assert "goal_id" not in abs_project
    assert "name" in abs_project
    assert "goal" not in abs_project
    assert "vision_id" not in abs_project
    assert pp.current_path(abs_project["project_id"]).exists()
    assert pp.current_path(cardio_project["project_id"]).exists()
    assert len(pp.load_history()) == 3
    assert len(pp.load_project_history(abs_project["project_id"])) == 1

    pp.save_plan(
        "Get visible abs",
        {"now": "again"},
        project_id=abs_project["project_id"],
        account_id=user["id"],
        event="chat",
    )
    assert pp.events_path(abs_project["project_id"]).read_text(encoding="utf-8").count("\n") == 2
    assert pp.events_path(cardio_project["project_id"]).read_text(encoding="utf-8").count("\n") == 1
    assert pp.load_current(abs_project["project_id"])["plan"]["now"] == "again"
    assert pp.load_current(abs_project["project_id"])["account_n"] == 1

    moved = pp.save_plan(
        "Improve cardio",
        {"now": "..."},
        project_id=cardio_project["project_id"],
        account_id=second_user["id"],
        event="owner_changed",
    )
    assert moved["account_n"] == 1  # first under second_user
    assert pp.load_current(abs_project["project_id"])["account_n"] == 1
    third = pp.save_plan("Stretch", {"now": "..."}, account_id=user["id"])
    assert third["account_n"] == 3  # gap from moved cardio not reused

    print("OK - user / current+events persistence behaves as expected")

    archive_dir = Path(tempfile.mkdtemp(prefix="archive_ops_test_"))
    _point_at(archive_dir)
    seat = ap.save_account("Parked")
    ap.archive_account(seat["id"])
    assert ap.get_account(seat["id"])["archived"] is True
    restored = ap.restore_account(seat["id"])
    assert restored is not None and not restored.get("archived")
    ap.archive_account(seat["id"])
    removed = ap.delete_account(seat["id"])
    assert removed is not None and removed["id"] == seat["id"]
    assert ap.get_account(seat["id"]) is None
    assert seat["id"] not in [a["id"] for a in ap.load_accounts()]
    assert ap.delete_account(seat["id"]) is None
    assert ap.restore_account(seat["id"]) is None
    after = ap.save_account("After delete")
    assert after["id"] == seat["id"] + 1  # deleted id is never reused

    gone = pp.save_plan("To erase", {"now": "x"}, account_id=None)
    assert pp.current_path(gone["project_id"]).exists()
    assert pp.delete_project(gone["project_id"]) is True
    assert not pp.current_path(gone["project_id"]).exists()
    assert pp.delete_project(gone["project_id"]) is False
    shutil.rmtree(archive_dir, ignore_errors=True)

    print("OK - account restore/delete and project erase behave as expected")

    from backend.project.panes.create.lifecycle import cancel_project, create_project

    names_dir = Path(tempfile.mkdtemp(prefix="default_names_test_"))
    _point_at(names_dir)
    assert create_project("", "1")["name"] == "New project 1"
    assert create_project("  ", "1")["name"] == "New project 2"
    assert create_project("", "2")["name"] == "New project 1"  # per account
    pp.save_plan("New project #7", {"now": "x"}, account_id=1)  # legacy form
    assert create_project("", "1")["name"] == "New project 8"
    assert create_project("Typed", "1")["name"] == "Typed"
    cancel_project(create_project("", "3")["project_id"])
    assert create_project("", "3")["name"] == "New project 1"  # archived don't count
    shutil.rmtree(names_dir, ignore_errors=True)

    print("OK - empty create name becomes the next New project N")

finally:
    storage_paths.DATA_DIR = _original_paths_data_dir
    for key, value in _original_pp.items():
        setattr(pp, key, value)
    for key, value in _original_ap.items():
        setattr(ap, key, value)
    shutil.rmtree(_tmp_dir, ignore_errors=True)
