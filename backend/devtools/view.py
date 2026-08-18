"""
A simple, static HTML snapshot of your saved goals/plans history -
useful if you want a file to look at without starting the Flask server
(see app.py, which serves the same page live at /history).

This is NOT the product's frontend - it's a personal debugging/
understanding tool. See docs/09-mvp.md § Testing philosophy for why the
real frontend is deliberately not being built yet.

Run from the PROJECT ROOT: .venv/bin/python -m backend.devtools.view
"""

import webbrowser

from backend.storage import DATA_DIR, ensure_data_dir, load_history
from backend.devtools.app import app, render_history_page

OUTPUT_FILE = DATA_DIR / "view.html"


if __name__ == "__main__":
    # render_template() needs an active Flask request context - not just
    # an app context - because the template calls url_for() to build the
    # CSS link. test_request_context() simulates a request without
    # actually starting the server; this reuses app.py's app (and
    # therefore its templates/ and static/ folders) instead of
    # duplicating that setup here.
    with app.test_request_context():
        html = render_history_page(load_history())

    ensure_data_dir()
    OUTPUT_FILE.write_text(html, encoding="utf-8")

    print(f"Wrote {OUTPUT_FILE}")
    webbrowser.open(f"file://{OUTPUT_FILE.resolve()}")
