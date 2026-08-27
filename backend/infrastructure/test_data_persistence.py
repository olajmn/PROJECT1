"""
Small, direct checks for the Vision persistence added 2026-08-26 -
not a test framework, just asserts run top to bottom (same style as
backend/goals/feedback/test_feedback_parser.py).

Runs entirely against a temporary directory, never the real data/ -
this module patches DATA_DIR/PLANS_FILE/VISIONS_FILE for the duration
of the run and restores them afterward, so it's safe to run against a
machine with real personal history in data/plans.json.

Run from the project root:
    .venv/bin/python -m backend.infrastructure.test_data_persistence
"""

import shutil
import tempfile
from pathlib import Path

from backend.infrastructure import data_persistence as dp

_original_data_dir = dp.DATA_DIR
_original_plans_file = dp.PLANS_FILE
_original_visions_file = dp.VISIONS_FILE

_tmp_dir = Path(tempfile.mkdtemp(prefix="data_persistence_test_"))
dp.DATA_DIR = _tmp_dir
dp.PLANS_FILE = _tmp_dir / "plans.json"
dp.VISIONS_FILE = _tmp_dir / "visions.json"

try:
    # A goal saved with no vision_id at all - the normal case - must
    # come back with vision_id present and None, not simply missing,
    # so every reader can rely on the key existing.
    plain_record = dp.save_plan("Make a song", {"right_now": "Write one line"})
    assert plain_record["vision_id"] is None, plain_record["vision_id"]

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
    abs_goal = dp.save_plan("Get visible abs", {"right_now": "..."}, vision_id=vision["id"])
    cardio_goal = dp.save_plan("Improve cardio", {"right_now": "..."}, vision_id=vision["id"])
    assert abs_goal["vision_id"] == cardio_goal["vision_id"] == vision["id"]
    assert abs_goal["goal_id"] != cardio_goal["goal_id"]  # still fully independent goals

    print("OK - vision persistence behaves as expected")
finally:
    dp.DATA_DIR = _original_data_dir
    dp.PLANS_FILE = _original_plans_file
    dp.VISIONS_FILE = _original_visions_file
    shutil.rmtree(_tmp_dir, ignore_errors=True)
