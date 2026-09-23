"""Checks for confirm_text(). Run from app/:

    .venv/bin/python -m backend.project.panes.canvas.see_map.test_confirm
"""

from backend.project.panes.canvas.see_map.confirm import (
    asks_to_see,
    confirm_text,
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
    assert asks_to_see("hva ser du") is True
    assert asks_to_see("tell me about this") is False

    focused = confirm_text(latest, "main.py", "p4", "what is this")
    assert focused == "Sample\n  src\n    main.py"

    whole = confirm_text(latest, "main.py", "p4", "what do you see")
    assert whole is not None
    assert "readme.txt" in whole

    quiet = confirm_text(latest, "main.py", "p4", "tell me about this")
    assert quiet is None
    assert confirm_text(latest, None, None, "tell me about this project") is None

    held = focus_labels(latest, "main.py", "p4")
    assert held == "Sample\n  src\n    main.py"

    status = map_status(latest)
    assert status.startswith("Sample")
    assert "readme.txt" in status
    assert map_status({"plan": {}}) == "The map is empty."

    empty = confirm_text(
        {"plan": {"progression": {"steps": []}}}, None, None, "hva ser du",
    )
    assert empty == "The map is empty."
    print("OK - confirm_text")


if __name__ == "__main__":
    main()
