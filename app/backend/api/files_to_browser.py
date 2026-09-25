"""
Hands the browser the app's own files: the HTML pages, JavaScript, and
CSS from app/ui/. Sends them as they are — no data, no model.

Everything under /api/... is requests_from_browser.py's job instead.
"""

# Contents
#  1. Settings
#      - UI_DIR
#      - CONTENT_TYPES
#
#  2. Sending a file
#      - send_page_file()
#      - _find_file()

from http.server import BaseHTTPRequestHandler
from pathlib import Path


# ============================================================
# 1. Settings
# ============================================================

# app/ui — parents: api -> backend -> app
UI_DIR = (Path(__file__).resolve().parents[2] / "ui").resolve()

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


# ============================================================
# 2. Sending a file
# ============================================================


def send_page_file(handler: BaseHTTPRequestHandler) -> None:
    """Answer one request with the file its address names, or 404.
    "/" opens the Projects page."""
    requested = "projects.html" if handler.path == "/" else handler.path.lstrip("/")
    file_path = _find_file(requested)
    if file_path is None:
        handler.send_error(404)
        return
    body = file_path.read_bytes()
    handler.send_response(200)
    handler.send_header(
        "Content-Type",
        CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"),
    )
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _find_file(requested: str) -> Path | None:
    """Map an address to a real file: ui/ root first (style.css,
    dist/…), then ui/pages/. Refuses anything outside app/ui/."""
    name = requested.lstrip("/")
    if not name or ".." in name.split("/"):
        return None
    for base in (UI_DIR, UI_DIR / "pages"):
        candidate = (base / name).resolve()
        try:
            candidate.relative_to(UI_DIR)
        except ValueError:
            return None
        if candidate.is_file():
            return candidate
    return None
