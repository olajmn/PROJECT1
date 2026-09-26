"""
Gets each request from the browser and runs the right function for it.

Two kinds of request:
- /api/... : an action or a read (create a project, add a node, send a
  chat message, ...). _POST_ROUTES lists which address runs which
  _handle_... method.
- anything else: a page, script, or stylesheet, handed out by
  files_to_browser.py.

server.py only starts the server; everything it answers is decided here.
"""

# Contents
#  1. Settings
#      - PORT
#
#  2. Which address runs what
#      - _POST_ROUTES
#
#  3. Handler
#      - do_GET() / do_POST()
#      - projects: create, rename, cancel, set user, timeline
#      - map: add node, remove node, paste, add folder, suggest
#      - chat: message (incl. slash-commands)
#      - users: create, archive
#      - shared helpers

import json
import re
from http.server import BaseHTTPRequestHandler

from backend.storage.users_persistence import load_users, rename_user, save_user
from backend.project.panes.chat.reply import reply
from backend.project.panes.create.lifecycle import cancel_project, create_project
from backend.project.panes.create.rename import rename_project
from backend.project.panes.create.resolver import get_latest_for_project
from backend.project.panes.canvas.add_folder import choose_folder
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.project.panes.create.project_user import archive_user, set_project_user
from backend.project.panes.canvas.edit_map import (
    add_map_node,
    import_map_folder,
    import_map_outline,
    remove_map_node,
    suggest_map_children,
)
from backend.model.client import MODEL, TEMPERATURE
from backend.api.activity_log import activity_log
from backend.project.timeline import project_timeline
from backend.api.files_to_browser import send_page_file
from backend.api.answers_to_browser import (
    active_projects,
    project_view,
    user_view,
)


# ============================================================
# 1. Settings
# ============================================================

PORT = 8000

_MODEL_FAILED = "that took longer than expected - try again in a moment"


# ============================================================
# 2. Which address runs what
# ============================================================

# Every POST address and the method that answers it. (\d+) is a project
# or user id, (p\d+) a map node id; both are passed to the method in
# order. Map, suggest, and chat paths use Project/Map/Talk names.
_POST_ROUTES = [
    (r"/api/projects", "_handle_create_project"),
    (r"/api/projects/(\d+)/name", "_handle_rename_project"),
    (r"/api/projects/(\d+)/cancel", "_handle_cancel_project"),
    (r"/api/projects/(\d+)/user", "_handle_set_project_user"),
    (r"/api/projects/(\d+)/map", "_handle_add_node"),
    (r"/api/projects/(\d+)/map/(p\d+)/remove", "_handle_remove_node"),
    (r"/api/projects/(\d+)/map/import", "_handle_paste_structure"),
    (r"/api/projects/(\d+)/map/folder", "_handle_add_folder"),
    (r"/api/projects/(\d+)/suggest/(p\d+)", "_handle_suggest_children"),
    (r"/api/projects/(\d+)/chat", "_handle_chat_message"),
    (r"/api/parse-outline-preview", "_handle_parse_outline_preview"),
    (r"/api/choose-folder", "_handle_choose_folder"),
    (r"/api/users", "_handle_create_user"),
    (r"/api/users/(\d+)/rename", "_handle_rename_user"),
    (r"/api/users/(\d+)/archive", "_handle_archive_user"),
]
_POST_ROUTES = [(re.compile(f"^{path}$"), method) for path, method in _POST_ROUTES]

# One project's history, oldest first (project/timeline.py).
_TIMELINE_ROUTE = re.compile(r"^/api/projects/(\d+)/timeline$")


# ============================================================
# 3. Handler
# ============================================================

class Handler(BaseHTTPRequestHandler):
    # Errors are sent as plain text, because the UI shows the error body
    # as-is; the default would be a whole HTML page.
    error_message_format = "%(message)s"
    error_content_type = "text/plain;charset=utf-8"

    def do_GET(self) -> None:
        if self.path == "/api/projects":
            self._send_json([project_view(r) for r in active_projects()])
        elif self.path == "/api/users":
            self._send_json([user_view(u) for u in load_users()])
        elif self.path == "/api/model":
            self._send_json({
                "provider": "ollama",
                "model": MODEL,
                "temperature": TEMPERATURE,
            })
        elif self.path == "/api/log":
            self._send_json(activity_log())
        elif match := _TIMELINE_ROUTE.match(self.path):
            self._handle_project_timeline(int(match.group(1)))
        else:
            send_page_file(self)

    def do_POST(self) -> None:
        for pattern, method in _POST_ROUTES:
            match = pattern.match(self.path)
            if match:
                args = [int(g) if g.isdigit() else g for g in match.groups()]
                getattr(self, method)(*args)
                return
        self.send_error(404)

    # --- projects ---------------------------------------------

    def _handle_create_project(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        text = (body.get("text") or "").strip()
        if not text:
            self.send_error(400, "empty text")
            return
        raw_sim = body.get("sim_user_id")
        sim_user_id = str(int(raw_sim)) if raw_sim is not None else ""
        self._send_json(project_view(create_project(text, sim_user_id)))

    def _handle_rename_project(self, project_id: int) -> None:
        text = self._read_text_body()
        if text is None:
            return
        record = rename_project(project_id, text)
        if record is None:
            self.send_error(404, "no such project")
            return
        self._send_json(project_view(record))

    def _handle_cancel_project(self, project_id: int) -> None:
        record = cancel_project(project_id)
        if record is None:
            self.send_error(404, "no such project, or already completed")
            return
        self._send_json(project_view(record))

    def _handle_set_project_user(self, project_id: int) -> None:
        """Body is {"sim_user_id": <int>}, or null to unlink."""
        body = self._read_json_body()
        if body is None:
            return
        raw_sim = body.get("sim_user_id")
        sim_user_id = int(raw_sim) if raw_sim is not None else None
        record = set_project_user(project_id, sim_user_id)
        if record is None:
            self.send_error(404, "no such project or user")
            return
        self._send_json(project_view(record))

    # --- map --------------------------------------------------

    def _handle_add_node(self, project_id: int) -> None:
        """One node the user named. No model call."""
        body = self._read_json_body()
        if body is None:
            return
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._save_map_change(lambda: add_map_node(
            latest,
            str(body.get("label") or ""),
            parent_id=_parent_id(body),
        ))

    def _handle_remove_node(self, project_id: int, node_id: str) -> None:
        """No model call."""
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._save_map_change(lambda: remove_map_node(latest, node_id))

    def _handle_paste_structure(self, project_id: int) -> None:
        """Pasted outline text, or an already-parsed `nodes` tree, becomes
        new nodes. No model call."""
        body = self._read_json_body()
        if body is None:
            return
        latest = self._load_project(project_id)
        if latest is None:
            return
        nodes = body.get("nodes")
        self._save_map_change(lambda: import_map_outline(
            latest,
            text=str(body.get("text") or "") if nodes is None else None,
            parent_id=_parent_id(body),
            unwrap=bool(body.get("unwrap", True)),
            forest=nodes,
        ))

    def _handle_add_folder(self, project_id: int) -> None:
        """One folder on this computer becomes nodes. No model call."""
        body = self._read_json_body()
        if body is None:
            return
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._save_map_change(lambda: import_map_folder(
            latest,
            str(body.get("path") or ""),
            parent_id=_parent_id(body),
        ))

    def _handle_suggest_children(self, project_id: int, node_id: str) -> None:
        """The model suggests child nodes under one node."""
        latest = self._load_project(project_id)
        if latest is None:
            return
        try:
            record = suggest_map_children(latest, node_id)
        except ValueError as e:
            self.send_error(422, str(e))
            return
        except Exception as e:
            self._model_failed(e)
            return
        self._send_json(project_view(record))

    def _handle_parse_outline_preview(self) -> None:
        """Paste structure's preview: the pasted text read both ways
        (title line dropped / kept). Nothing is saved; no project needed."""
        body = self._read_json_body()
        if body is None:
            return
        text = str(body.get("text") or "")
        self._send_json({
            "stripped": parse_outline(text, unwrap=True),
            "kept": parse_outline(text, unwrap=False),
        })

    def _handle_choose_folder(self) -> None:
        """Opens the macOS folder dialog. Cancel returns an empty path."""
        try:
            path = choose_folder()
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json({"path": path})

    # --- chat -------------------------------------------------

    def _handle_chat_message(self, project_id: int) -> None:
        body = self._read_json_body()
        if body is None:
            return
        note = (body.get("text") or "").strip()
        if not note:
            self.send_error(400, "empty text")
            return
        latest = self._load_project(project_id)
        if latest is None:
            return
        try:
            result = reply(
                latest,
                note,
                map_focus=_clean(body.get("focus_label")),
                focus_step_id=_clean(body.get("focus_step_id")),
            )
        except Exception as e:
            self._model_failed(e)
            return
        self._send_json(
            project_view(
                result["record"],
                reply=result["reply"],
                select=result.get("select"),
            )
        )

    def _handle_project_timeline(self, project_id: int) -> None:
        """Everything that happened in one project, oldest first."""
        if self._load_project(project_id) is None:
            return
        self._send_json(project_timeline(project_id))

    # --- users ------------------------------------------------

    def _handle_create_user(self) -> None:
        text = self._read_text_body()
        if text is None:
            return
        self._send_json(user_view(save_user(text)))

    def _handle_rename_user(self, sim_user_id: int) -> None:
        body = self._read_json_body()
        if body is None:
            return
        if "text" not in body:
            self.send_error(400, "missing text")
            return
        user = rename_user(sim_user_id, str(body.get("text") or ""))
        if user is None:
            self.send_error(404, "no such user")
            return
        self._send_json(user_view(user))

    def _handle_archive_user(self, sim_user_id: int) -> None:
        user = archive_user(sim_user_id)
        if user is None:
            self.send_error(404, "no such user")
            return
        self._send_json(user_view(user))

    # --- shared helpers ---------------------------------------

    def _read_json_body(self) -> dict | None:
        """The request body as a dict, or None after answering 400."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return None

    def _read_text_body(self) -> str | None:
        """The body's non-empty `text`, or None after answering 400."""
        body = self._read_json_body()
        if body is None:
            return None
        text = (body.get("text") or "").strip()
        if not text:
            self.send_error(400, "empty text")
            return None
        return text

    def _load_project(self, project_id: int) -> dict | None:
        """The project's latest record, or None after answering 404."""
        latest = get_latest_for_project(project_id)
        if latest is None:
            self.send_error(404, "no such project")
        return latest

    def _save_map_change(self, change) -> None:
        """Run one map edit and answer with the project. A ValueError
        (e.g. an unknown node id) becomes 422."""
        try:
            record = change()
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(project_view(record))

    def _model_failed(self, error: Exception) -> None:
        """One failed model call must not crash the server; the user
        gets a fixed message, the terminal gets the real error."""
        print(f"(debug: {error})")
        self.send_error(503, _MODEL_FAILED)

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass  # keep the terminal for debug lines, not HTTP access logs


def _parent_id(body: dict) -> str | None:
    """Optional parent node id for map edits; None means top level."""
    return _clean(body.get("parent_id"))


def _clean(raw) -> str | None:
    """A trimmed string, or None when missing or blank."""
    text = str(raw).strip() if raw else ""
    return text or None
