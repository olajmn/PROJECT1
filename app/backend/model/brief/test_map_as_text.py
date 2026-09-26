"""Checks for map_status() and focus_labels(). Run from app/:

    .venv/bin/python -m backend.model.brief.test_map_as_text
"""

from backend.model.brief.map_as_text import (
    focus_labels,
    map_status,
)


def main() -> None:
    latest = {
        "plan": {
            "progression": {
                "steps": [
                    {
                        "id": "p1",
                        "label": "Sample",
                        "children": [
                            {
                                "id": "p2",
                                "label": "src",
                                "children": [
                                    {"id": "p4", "label": "main.py", "children": []},
                                ],
                            },
                            {"id": "p3", "label": "readme.txt", "children": []},
                        ],
                    }
                ]
            }
        }
    }
    held = focus_labels(latest, "main.py", "p4")
    assert held == "Sample\n  src\n    main.py"
    assert focus_labels(latest, "loose", None) == "loose"
    assert focus_labels(latest, None, None) is None

    status = map_status(latest)
    assert status.startswith("Sample")
    assert "readme.txt" in status
    assert map_status({"plan": {}}) == "The map is empty."
    print("OK - map_status / focus_labels")


if __name__ == "__main__":
    main()
