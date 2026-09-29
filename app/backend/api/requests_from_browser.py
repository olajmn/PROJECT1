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
#      - map: add node, remove node, move node, paste, add folder
#      - saved trees: save, list, insert, delete
#      - chat: message (incl. slash-commands)
#      - accounts: create, rename, archive
#      - shared helpers

import json
import re
from datetime import date
from http.server import BaseHTTPRequestHandler

from backend.storage.accounts_persistence import (
    delete_account,
    load_accounts,
    rename_account,
    restore_account,
    save_account,
)
from backend.project.panes.chat.reply import reply
from backend.project.panes.create.lifecycle import (
    cancel_project,
    create_project,
    delete_project,
    restore_project,
)
from backend.project.panes.create.rename import rename_project
from backend.project.panes.create.resolver import get_latest_for_project
from backend.project.panes.canvas.add_folder import choose_folder
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.project.panes.create.project_account import archive_account, set_project_user
from backend.project.panes.canvas.edit_map import (
    add_map_node,
    import_map_folder,
    import_map_outline,
    move_map_node,
    remove_map_node,
)
from backend.project.saved_trees import (
    insert_saved_tree,
    remove_saved_tree,
    save_tree_from_node,
    saved_trees_for,
)
from backend.model.client import MODEL, TEMPERATURE
from backend.api.activity_log import activity_log
from backend.project.timeline import project_timeline
from backend.api.files_to_browser import send_page_file
from backend.api.answers_to_browser import (
    account_view,
    active_projects,
    archived_projects,
    project_view,
    saved_tree_view,
)


# ============================================================
# 1. Settings
# ============================================================

PORT = 8000

_MODEL_FAILED = "that took longer than expected - try again in a moment"
_MODEL_UNREACHABLE = "the model is not running - start Ollama and try again"


# ============================================================
# 2. Which address runs what
# ============================================================

# Every POST address and the method that answers it. (\d+) is a project
# or user id, (p\d+) a map node id, (t\d+) a saved tree id; all are
# passed to the method in order. Map and chat paths use Project/Map/Talk names.
_POST_ROUTES = [
    (r"/api/projects", "_handle_create_project"),
    (r"/api/projects/(\d+)/name", "_handle_rename_project"),
    (r"/api/projects/(\d+)/cancel", "_handle_cancel_project"),
    (r"/api/projects/(\d+)/restore", "_handle_restore_project"),
    (r"/api/projects/(\d+)/delete", "_handle_delete_project"),
    (r"/api/projects/(\d+)/user", "_handle_set_project_user"),
    (r"/api/projects/(\d+)/map", "_handle_add_node"),
    (r"/api/projects/(\d+)/map/(p\d+)/remove", "_handle_remove_node"),
    (r"/api/projects/(\d+)/map/(p\d+)/move-(up|down)", "_handle_move_node"),
    (r"/api/projects/(\d+)/map/import", "_handle_paste_structure"),
    (r"/api/projects/(\d+)/map/folder", "_handle_add_folder"),
    (r"/api/projects/(\d+)/map/(p\d+)/save-tree", "_handle_save_tree"),
    (r"/api/projects/(\d+)/map/insert-tree", "_handle_insert_tree"),
    (r"/api/saved-trees/(t\d+)/delete", "_handle_delete_saved_tree"),
    (r"/api/projects/(\d+)/chat", "_handle_chat_message"),
    (r"/api/parse-outline-preview", "_handle_parse_outline_preview"),
    (r"/api/choose-folder", "_handle_choose_folder"),
    (r"/api/accounts", "_handle_create_account"),
    (r"/api/accounts/(\d+)/rename", "_handle_rename_account"),
    (r"/api/accounts/(\d+)/archive", "_handle_archive_account"),
    (r"/api/accounts/(\d+)/restore", "_handle_restore_account"),
    (r"/api/accounts/(\d+)/delete", "_handle_delete_account"),
]
_POST_ROUTES = [(re.compile(f"^{path}$"), method) for path, method in _POST_ROUTES]

# The activity log, one page at a time: /api/log or /api/log?offset=N.
_LOG_ROUTE = re.compile(r"^/api/log(?:\?offset=(\d+))?$")

# One project's history, oldest first (project/timeline.py).
_TIMELINE_ROUTE = re.compile(r"^/api/projects/(\d+)/timeline$")

# The saved trees of one project's account (project/saved_trees/).
_SAVED_TREES_ROUTE = re.compile(r"^/api/projects/(\d+)/saved-trees$")


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
        elif self.path == "/api/projects/archived":
            self._send_json([project_view(r) for r in archived_projects()])
        elif self.path == "/api/accounts":
            self._send_json([account_view(u) for u in load_accounts()])
        elif self.path == "/api/model":
            self._send_json({
                "provider": "ollama",
                "model": MODEL,
                "temperature": TEMPERATURE,
            })
        elif match := _LOG_ROUTE.match(self.path):
            self._send_json(activity_log(int(match.group(1) or 0)))
        elif match := _TIMELINE_ROUTE.match(self.path):
            self._handle_project_timeline(int(match.group(1)))
        elif match := _SAVED_TREES_ROUTE.match(self.path):
            self._handle_list_saved_trees(int(match.group(1)))
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
        # Empty text is allowed: create_project() picks `New project N`.
        text = (body.get("text") or "").strip()
        raw_account = body.get("account_id")
        account_id = str(int(raw_account)) if raw_account is not None else ""
        self._send_json(project_view(create_project(text, account_id)))

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

    def _handle_restore_project(self, project_id: int) -> None:
        record = restore_project(project_id)
        if record is None:
            self.send_error(404, "no such project, or completed")
            return
        self._send_json(project_view(record))

    def _handle_delete_project(self, project_id: int) -> None:
        if not delete_project(project_id):
            self.send_error(404, "no such project")
            return
        self._send_json({"ok": True, "project_id": project_id})

    def _handle_set_project_user(self, project_id: int) -> None:
        """Body is {"account_id": <int>}, or null to unlink."""
        body = self._read_json_body()
        if body is None:
            return
        raw_account = body.get("account_id")
        account_id = int(raw_account) if raw_account is not None else None
        record = set_project_user(project_id, account_id)
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

    def _handle_move_node(self, project_id: int, node_id: str, direction: str) -> None:
        """One place up or down among its siblings. No model call."""
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._save_map_change(lambda: move_map_node(latest, node_id, direction))

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

    # --- saved trees ------------------------------------------

    def _handle_save_tree(self, project_id: int, node_id: str) -> None:
        """This node and everything under it, as structure. No model call."""
        latest = self._load_project(project_id)
        if latest is None:
            return
        try:
            saved = save_tree_from_node(latest, node_id)
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(saved_tree_view(saved))

    def _handle_list_saved_trees(self, project_id: int) -> None:
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._send_json([saved_tree_view(t) for t in saved_trees_for(latest)])

    def _handle_insert_tree(self, project_id: int) -> None:
        """A saved tree becomes new nodes (fresh ids). No model call."""
        body = self._read_json_body()
        if body is None:
            return
        latest = self._load_project(project_id)
        if latest is None:
            return
        self._save_map_change(lambda: insert_saved_tree(
            latest,
            str(body.get("tree_id") or ""),
            _parent_id(body),
        ))

    def _handle_delete_saved_tree(self, tree_id: str) -> None:
        try:
            removed = remove_saved_tree(tree_id)
        except ValueError as e:
            self.send_error(404, str(e))
            return
        self._send_json(saved_tree_view(removed))

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
                focus_day=_day(body.get("focus_day")),
            )
        except Exception as e:
            self._model_failed(e)
            return
        self._send_json(
            project_view(
                result["record"],
                select=result.get("select"),
                toggle_map_ids=bool(result.get("toggle_map_ids")),
            )
        )

    def _handle_project_timeline(self, project_id: int) -> None:
        """Everything that happened in one project, oldest first."""
        if self._load_project(project_id) is None:
            return
        self._send_json(project_timeline(project_id))

    # --- accounts ---------------------------------------------

    def _handle_create_account(self) -> None:
        text = self._read_text_body()
        if text is None:
            return
        self._send_json(account_view(save_account(text)))

    def _handle_rename_account(self, account_id: int) -> None:
        body = self._read_json_body()
        if body is None:
            return
        if "text" not in body:
            self.send_error(400, "missing text")
            return
        account = rename_account(account_id, str(body.get("text") or ""))
        if account is None:
            self.send_error(404, "no such account")
            return
        self._send_json(account_view(account))

    def _handle_archive_account(self, account_id: int) -> None:
        account = archive_account(account_id)
        if account is None:
            self.send_error(404, "no such account")
            return
        self._send_json(account_view(account))

    def _handle_restore_account(self, account_id: int) -> None:
        account = restore_account(account_id)
        if account is None:
            self.send_error(404, "no such account")
            return
        self._send_json(account_view(account))

    def _handle_delete_account(self, account_id: int) -> None:
        account = delete_account(account_id)
        if account is None:
            self.send_error(404, "no such account")
            return
        self._send_json(account_view(account))

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
        # ollama raises the builtin ConnectionError when nothing listens.
        unreachable = isinstance(error, ConnectionError)
        self.send_error(503, _MODEL_UNREACHABLE if unreachable else _MODEL_FAILED)

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


def _day(raw) -> str | None:
    """A YYYY-MM-DD day, or None when missing or not a date."""
    text = _clean(raw)
    if text is None:
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None
