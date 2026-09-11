"""
Minimal HTTP transport for agent/ - the smallest boundary that lets a
browser reach the already-established USER -> LLM1 -> LLM2 -> LLM3 ->
Planning flow (cli.py's process_turn()) over HTTP instead of a
terminal. Pure transport: serves ui/'s static files, parses one JSON
request, calls process_turn(), serializes the result. No planning
logic, no LLM logic, no session/state decisions of its own beyond what
process_turn()/Session already own.

Stdlib only (http.server) - no new dependency, matching agent/'s
requirements.txt ("ollama" only, nothing added for this).

Single, process-wide Session - deliberately NOT per-browser/per-user.
This is the same limitation cli.py already had (one session per
process); server.py does not solve multi-session/context, it only
exposes the same single conversation over HTTP instead of a terminal.
See the accompanying report for what this means and doesn't mean.

Run from agent/ (this directory), with agent/'s own venv:
    .venv/bin/python server.py
Then open http://localhost:8000/ in a browser.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cli import Session, process_turn

UI_DIR = (Path(__file__).parent / "ui").resolve()
PORT = 8000

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}

session = Session()  # process-wide - see module docstring


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        requested = "index.html" if self.path == "/" else self.path.lstrip("/")
        file_path = (UI_DIR / requested).resolve()
        if UI_DIR not in file_path.parents or not file_path.is_file():
            self.send_error(404)
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/message":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
            user_text = (payload_in.get("text") or "").strip()
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        if not user_text:
            self.send_error(400, "empty text")
            return

        try:
            result = process_turn(session, user_text)
        except Exception as e:  # transport must not crash on one bad turn
            result = {
                "understanding": None, "capability": None, "surface": None,
                "node": None, "goal_id": None, "reply": f"(error: {e})",
            }

        body = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass  # keep the terminal for the conversation, not HTTP access logs


if __name__ == "__main__":
    print(f"web prototype - http://localhost:{PORT}/")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
