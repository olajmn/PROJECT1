"""Checks for folder_tree(). Run from app/:

    .venv/bin/python -m backend.project.panes.canvas.add_folder.test_walk
"""

import tempfile
from pathlib import Path

from backend.project.panes.canvas.add_folder.walk import folder_tree


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "Sample"
        nested = root / "src"
        nested.mkdir(parents=True)
        (nested / "main.py").write_text("print(1)\n", encoding="utf-8")
        (root / "readme.txt").write_text("hi\n", encoding="utf-8")
        (root / ".hidden").write_text("no\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "pkg.js").write_text("", encoding="utf-8")

        forest = folder_tree(str(root))
        assert len(forest) == 1
        top = forest[0]
        assert top["label"] == "Sample"
        assert top["path"] == str(root.resolve())
        labels = [child["label"] for child in top["children"]]
        assert labels == ["src", "readme.txt"]
        assert top["children"][0]["children"][0]["label"] == "main.py"
        assert top["children"][0]["children"][0]["path"].endswith("main.py")

    try:
        folder_tree(str(Path(raw) / "missing"))
    except ValueError as e:
        assert "not found" in str(e)
    else:
        raise AssertionError("missing folder should fail")

    print("OK - folder_tree")


if __name__ == "__main__":
    main()
