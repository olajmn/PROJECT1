"""
HTTP handler — route /api/* to agent/project/store and serve ui/ static files.

server.py is only the process entry; this module owns the request surface.
"""

# Contents
#  1. Configuration
#      - UI_DIR, PORT, CONTENT_TYPES
#      - path regexes
#      - _resolve_ui_file()
#
#  2. Handler
#      - Handler (do_GET / do_POST / route handlers)

import json
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from backend.store.data_persistence import load_users, save_user
from backend.store.session import load_sessions
from backend.project.panes.chat.turn import take_turn
from backend.project.panes.create.lifecycle import (
    cancel_goal,
    create_empty_project,
    create_goal,
)
from backend.project.panes.create.resolver import get_latest_for_goal
from backend.project.panes.canvas.add_folder import choose_folder
from backend.project.panes.canvas.call_read import read_tree
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.project.engine.planner import archive_user, set_project_user
from backend.project.panes.canvas.edit_map import (
    add_progression_bead,
    import_progression_folder,
    import_progression_outline,
    remove_progression_bead,
    zoom_progression_step,
)
from backend.llm_client import MODEL, TEMPERATURE
from backend.api.views import (
    active_goals,
    goal_view,
    user_view,
)


# ============================================================
# 1. Configuration
# ============================================================

# app/ui — parents: api -> backend -> app
UI_DIR = (Path(__file__).resolve().parents[2] / "ui").resolve()
PORT = 8000

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}

_FEEDBACK_PATH_RE = re.compile(r"^/api/projects/(\d+)/feedback$")
_CANCEL_PATH_RE = re.compile(r"^/api/projects/(\d+)/cancel$")
_PROJECT_USER_PATH_RE = re.compile(r"^/api/projects/(\d+)/user$")
_GOAL_ZOOM_PATH_RE = re.compile(r"^/api/projects/(\d+)/zoom/(p\d+)$")
_GOAL_PROGRESSION_PATH_RE = re.compile(r"^/api/projects/(\d+)/progression$")
_GOAL_READ_PATH_RE = re.compile(r"^/api/projects/(\d+)/read$")
_GOAL_PROGRESSION_IMPORT_RE = re.compile(
    r"^/api/projects/(\d+)/progression/import$",
)
_GOAL_PROGRESSION_FOLDER_RE = re.compile(
    r"^/api/projects/(\d+)/progression/folder$",
)
_GOAL_PROGRESSION_REMOVE_RE = re.compile(
    r"^/api/projects/(\d+)/progression/(p\d+)/remove$",
)
_USER_ARCHIVE_PATH_RE = re.compile(r"^/api/users/(\d+)/archive$")


def _resolve_ui_file(requested: str) -> Path | None:
    """Map a URL path under ui/ to a real file.

    Looks in order: ui/ root (style.css, dist/…), then ui/pages/.
    Rejects paths that escape UI_DIR.
    """
    name = requested.lstrip("/")
    if not name or ".." in name.split("/"):
        return None
    for base in (UI_DIR, UI_DIR / "pages"):
        candidate = (base / name).resolve()
        try:
            candidate.relative_to(UI_DIR.resolve())
        except ValueError:
            return None
        if candidate.is_file():
            return candidate
    return None


# ============================================================
# 2. Handler
# ============================================================

class Handler(BaseHTTPRequestHandler):
    # send_error()'s default renders a full HTML page (BaseHTTPRequestHandler's
    # own DEFAULT_ERROR_MESSAGE) with the real reason buried in a <p> tag -
    # ui/'s error handling just shows send_error()'s raw response body, so
    # every 4xx/5xx from this server was displaying that HTML soup instead
    # of the actual message. Plain text here fixes every route's error
    # display at once, not just one caller.
    error_message_format = "%(message)s"
    error_content_type = "text/plain;charset=utf-8"

    def do_GET(self) -> None:
        if self.path == "/api/projects":
            self._send_json([goal_view(r) for r in active_goals()])
            return
        if self.path == "/api/users":
            self._send_json([user_view(u) for u in load_users()])
            return
        if self.path == "/api/model":
            # Same dials llm_client uses for every call — read-only inspect.
            self._send_json({
                "provider": "ollama",
                "model": MODEL,
                "temperature": TEMPERATURE,
            })
            return
        if self.path == "/api/sessions":
            # Process-run bookkeeping (data/sessions.json), newest first.
            self._send_json(list(reversed(load_sessions())))
            return
        # Project workspace is the product home; HTML lives under
        # ui/pages/. URLs stay /projects.html etc.
        requested = "projects.html" if self.path == "/" else self.path.lstrip("/")
        file_path = _resolve_ui_file(requested)
        if file_path is None:
            self.send_error(404)
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path == "/api/projects":
            self._handle_create_goal()
            return
        if self.path == "/api/users":
            self._handle_create_user()
            return
        if self.path == "/api/parse-outline-preview":
            self._handle_parse_outline_preview()
            return
        if self.path == "/api/choose-folder":
            self._handle_choose_folder()
            return
        goal_zoom_match = _GOAL_ZOOM_PATH_RE.match(self.path)
        if goal_zoom_match:
            self._handle_goal_zoom(
                int(goal_zoom_match.group(1)), goal_zoom_match.group(2),
            )
            return
        goal_progression_import_match = _GOAL_PROGRESSION_IMPORT_RE.match(
            self.path,
        )
        if goal_progression_import_match:
            self._handle_import_progression(
                int(goal_progression_import_match.group(1)),
            )
            return
        goal_progression_folder_match = _GOAL_PROGRESSION_FOLDER_RE.match(
            self.path,
        )
        if goal_progression_folder_match:
            self._handle_import_folder(
                int(goal_progression_folder_match.group(1)),
            )
            return
        goal_read_match = _GOAL_READ_PATH_RE.match(self.path)
        if goal_read_match:
            self._handle_read_tree(int(goal_read_match.group(1)))
            return
        goal_progression_match = _GOAL_PROGRESSION_PATH_RE.match(self.path)
        if goal_progression_match:
            self._handle_add_progression(int(goal_progression_match.group(1)))
            return
        goal_remove_match = _GOAL_PROGRESSION_REMOVE_RE.match(self.path)
        if goal_remove_match:
            self._handle_remove_progression(
                int(goal_remove_match.group(1)), goal_remove_match.group(2),
            )
            return
        feedback_match = _FEEDBACK_PATH_RE.match(self.path)
        if feedback_match:
            self._handle_goal_feedback(int(feedback_match.group(1)))
            return
        cancel_match = _CANCEL_PATH_RE.match(self.path)
        if cancel_match:
            self._handle_cancel_goal(int(cancel_match.group(1)))
            return
        project_user_match = _PROJECT_USER_PATH_RE.match(self.path)
        if project_user_match:
            self._handle_set_project_user(int(project_user_match.group(1)))
            return
        archive_match = _USER_ARCHIVE_PATH_RE.match(self.path)
        if archive_match:
            self._handle_archive_user(int(archive_match.group(1)))
            return
        self.send_error(404)

    def _read_text_body(self) -> str | None:
        """The `{"text": ...}` body every POST route here shares -
        None (after sending its own error response) if the body is
        missing, malformed, or empty once stripped."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return None
        text = (payload_in.get("text") or "").strip()
        if not text:
            self.send_error(400, "empty text")
            return None
        return text

    def _handle_create_goal(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        text = (payload_in.get("text") or "").strip()
        if not text:
            self.send_error(400, "empty text")
            return
        raw_sim = payload_in.get("sim_user_id")
        sim_user_id_value = (
            str(int(raw_sim)) if raw_sim is not None else ""
        )
        # `planned: false` mints a named project with no plan - the text
        # is a label, not a goal for the planner to work from.
        if payload_in.get("planned") is False:
            self._send_json(
                goal_view(create_empty_project(text, sim_user_id_value)),
            )
            return
        try:
            record = create_goal(text, "", sim_user_id_value)
        except Exception as e:  # transport must not crash on one bad turn
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(goal_view(record))

    def _handle_goal_zoom(self, goal_id: int, step_id: str) -> None:
        """One level deeper under a Step in plan.progression — persists
        on the Goal so the Projects map grows."""
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            record = zoom_progression_step(latest, step_id)
        except ValueError as e:
            self.send_error(422, str(e))
            return
        except Exception as e:
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(goal_view(record))

    def _handle_add_progression(self, goal_id: int) -> None:
        """Append one user-named bead to plan.progression — no model."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            parent_raw = payload_in.get("parent_id")
            parent_id = str(parent_raw).strip() if parent_raw else None
            record = add_progression_bead(
                latest,
                str(payload_in.get("label") or ""),
                parent_id=parent_id or None,
            )
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(goal_view(record))

    def _handle_read_tree(self, goal_id: int) -> None:
        """Read the WHAT tree back into a summary. Nothing is
        written — the reading is returned and then gone, until we know
        whether these are worth keeping."""
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        steps = (latest.get("plan") or {}).get("progression", {}).get("steps")
        if not isinstance(steps, list) or not steps:
            self.send_error(400, "nothing to read - the map is empty")
            return
        try:
            reading = read_tree(latest["goal"], steps)
        except Exception as e:  # transport must not crash on one bad call
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        if reading is None:
            self.send_error(503, "no reading came back - try again")
            return
        self._send_json(reading)

    def _handle_import_progression(self, goal_id: int) -> None:
        """Parse a pasted outline/ASCII tree into new beads — no model."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            parent_raw = payload_in.get("parent_id")
            parent_id = str(parent_raw).strip() if parent_raw else None
            nodes = payload_in.get("nodes")
            record = import_progression_outline(
                latest,
                text=str(payload_in.get("text") or "") if nodes is None else None,
                parent_id=parent_id or None,
                unwrap=bool(payload_in.get("unwrap", True)),
                forest=nodes,
            )
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(goal_view(record))

    def _handle_choose_folder(self) -> None:
        """Open the macOS folder dialog. Cancel returns an empty path."""
        try:
            path = choose_folder()
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json({"path": path})

    def _handle_import_folder(self, goal_id: int) -> None:
        """Walk one folder into new beads — no model."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            parent_raw = payload_in.get("parent_id")
            parent_id = str(parent_raw).strip() if parent_raw else None
            record = import_progression_folder(
                latest,
                str(payload_in.get("path") or ""),
                parent_id=parent_id or None,
            )
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(goal_view(record))

    def _handle_parse_outline_preview(self) -> None:
        """Dry-run parse_outline() both ways (title line dropped / kept)
        so ui/ can show the user what Paste structure would create
        before they commit to one - no model call, no goal needed."""
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        text = str(payload_in.get("text") or "")
        self._send_json({
            "stripped": parse_outline(text, unwrap=True),
            "kept": parse_outline(text, unwrap=False),
        })

    def _handle_remove_progression(self, goal_id: int, step_id: str) -> None:
        """Drop one bead from plan.progression — no model."""
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            record = remove_progression_bead(latest, step_id)
        except ValueError as e:
            self.send_error(422, str(e))
            return
        self._send_json(goal_view(record))

    def _handle_goal_feedback(self, goal_id: int) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        note = (payload_in.get("text") or "").strip()
        if not note:
            self.send_error(400, "empty text")
            return
        focus_raw = payload_in.get("focus_label")
        map_focus = str(focus_raw).strip() if focus_raw else None
        step_raw = payload_in.get("focus_step_id")
        focus_step_id = str(step_raw).strip() if step_raw else None
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            result = take_turn(
                latest,
                note,
                map_focus=map_focus or None,
                focus_step_id=focus_step_id or None,
            )
        except Exception as e:  # transport must not crash on one bad turn
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(goal_view(result["record"], reply=result["reply"]))

    def _handle_cancel_goal(self, goal_id: int) -> None:
        # No request body - same reasoning as _handle_archive_user():
        # the goal is already named by id in the path. planner.
        # cancel_goal() is a pure state transition (no model call), so
        # there's nothing to retry here, unlike _handle_goal_feedback().
        record = cancel_goal(goal_id)
        if record is None:
            self.send_error(404, "no such goal, or already completed")
            return
        self._send_json(goal_view(record))

    def _handle_set_project_user(self, goal_id: int) -> None:
        # Body is {"sim_user_id": <int>} or {"sim_user_id": null} to
        # remove the link - not {"text": ...} like every other POST
        # route here, so this doesn't go through _read_text_body(). No
        # model call, same as _handle_cancel_goal() - a pure state
        # transition.
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        raw_sim = payload_in.get("sim_user_id")
        sim_user_id = int(raw_sim) if raw_sim is not None else None
        record = set_project_user(goal_id, sim_user_id)
        if record is None:
            self.send_error(404, "no such project or user")
            return
        self._send_json(goal_view(record))

    def _handle_create_user(self) -> None:
        text = self._read_text_body()
        if text is None:
            return
        user = save_user(text)  # pure append, no model call - nothing to retry
        self._send_json(user_view(user))

    def _handle_archive_user(self, sim_user_id: int) -> None:
        # No request body - archiving names the user by id in the path.
        user = archive_user(sim_user_id)
        if user is None:
            self.send_error(404, "no such user")
            return
        self._send_json(user_view(user))

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass  # keep the terminal for the conversation, not HTTP access logs


