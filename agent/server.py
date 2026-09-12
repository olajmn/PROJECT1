"""
Minimal HTTP transport for agent/ - the smallest boundary that lets a
browser reach Planning over HTTP instead of a terminal. Pure
transport: serves ui/'s static files, parses JSON requests,
serializes results. No planning logic, no LLM logic of its own.

Two distinct paths into Planning, deliberately different shapes:

- POST /api/message - free conversation (cli.py's process_turn():
  Node 1 -> Node 2 -> Node 3 -> Planning -> Node 1), for when which
  goal (or whether Planning applies at all) isn't already known. Uses
  the single, process-wide `session` below.
- GET/POST /api/goals[/<id>/feedback, /<id>/cancel, /<id>/vision],
  GET /api/goals/completed, GET /api/history,
  GET/POST /api/visions[/<id>/archive] - known
  capability context (see
  docs/03-architecture.md Part 3 § 3): the goal_id (where one applies)
  is already given explicitly, by the caller, not inferred from
  session state or guessed by a Node - so these call planner.py/
  data_persistence.py directly, skip Node 1/2/3 entirely, and are
  immune to the topic-continuity defect docs/04-current-state.md § 5
  documents for the free-conversation path. No natural-language
  voicing (Node 1) on these responses either - see manifestation.py's
  own surface_text()/to_planning_node(), already deterministic and
  already what ui/active.html shows directly.
- GET/POST /api/session - the manual bridge between the two paths
  above: reads or overwrites the free-conversation `session`'s own
  `current_goal_id`, otherwise invisible and unsettable from any page.
  Lets e.g. Active point the chat at a specific existing goal instead
  of only ever guessing - still doesn't address § 5's mid-conversation
  topic-switch defect itself, only gives an explicit, visible starting
  point.
- GET /api/sessions - every persisted Session record (one per real run
  of cli.py's main() or this file), each with its "what happened"
  derived at read time from load_history()/load_visions() filtered to
  that Session's own time window, rather than a new write-path logged
  by every mutating route above.

Stdlib only (http.server) - no new dependency, matching agent/'s
requirements.txt ("ollama" only, nothing added for this).

Single, process-wide Session for /api/message only - deliberately NOT
per-browser/per-user. This is the same limitation cli.py already had
(one session per process); server.py does not solve multi-session/
context for free conversation, it only exposes the same single
conversation over HTTP instead of a terminal.

Run from agent/ (this directory), with agent/'s own venv:
    .venv/bin/python server.py
Then open http://localhost:8000/ in a browser.
"""

# Contents
#
#  1. Configuration
#      - UI_DIR, PORT
#      - _CONTENT_TYPES
#      - _FEEDBACK_PATH_RE, _CANCEL_PATH_RE, _GOAL_VISION_PATH_RE,
#        _VISION_ARCHIVE_PATH_RE
#      - session (process-wide, /api/message only)
#
#  2. View builders
#      - _goal_view()
#      - _active_goals()
#      - _completed_goals()
#      - _HISTORY_PLAN_FIELDS
#      - _history_view()
#      - _session_view()
#      - _session_goal_event()
#      - _session_vision_event()
#      - _session_log_view()
#      - _vision_view()
#
#  3. HTTP handler
#      - Handler
#          - do_GET()
#          - do_POST()
#          - _read_text_body()
#          - _handle_message()
#          - _handle_create_goal()
#          - _handle_goal_feedback()
#          - _handle_cancel_goal()
#          - _handle_set_goal_vision()
#          - _handle_set_session()
#          - _handle_create_vision()
#          - _handle_archive_vision()
#          - _send_json()
#          - log_message()
#
#  4. Entry point

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cli import Session, process_turn
from backend.manifestation import surface_text, to_planning_node
from backend.infrastructure.data_persistence import load_history, load_sessions, load_visions, save_vision
from backend.planning.goal.resolver import created_at_key, get_latest_for_all_goals, get_latest_for_goal
from backend.planning.plan.planner import apply_feedback, archive_vision, cancel_goal, create_goal, set_goal_vision

# 1. Configuration

UI_DIR = (Path(__file__).parent / "ui").resolve()
PORT = 8000

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}

_FEEDBACK_PATH_RE = re.compile(r"^/api/goals/(\d+)/feedback$")
_CANCEL_PATH_RE = re.compile(r"^/api/goals/(\d+)/cancel$")
_GOAL_VISION_PATH_RE = re.compile(r"^/api/goals/(\d+)/vision$")
_VISION_ARCHIVE_PATH_RE = re.compile(r"^/api/visions/(\d+)/archive$")

session = Session()  # process-wide - see module docstring, /api/message only

# 2. View builders


def _goal_view(record: dict) -> dict:
    """The one shape every /api/goals response uses for a single goal
    - record fields a UI actually needs (identity, display text,
    completion) plus the same manifestation.py translation
    /api/message already relies on, so ui/active.ts and ui/src/main.ts
    render an identical plan tree from an identical shape."""
    try:
        node = to_planning_node(record)
    except Exception as e:
        # A record saved before plan_structure.py's steps-with-
        # microsteps shape (2026-09-11) still has plan.steps as flat
        # strings, which to_planning_node() no longer understands -
        # show the goal without a tree rather than losing the whole
        # /api/goals list over one legacy record.
        print(f"(debug: to_planning_node() failed for goal {record.get('goal_id')}: {e})")
        node = None
    return {
        "goal_id": record["goal_id"],
        "goal": record["goal"],
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "vision_id": record.get("vision_id"),
        "surface": surface_text(record),
        "node": node,
    }


def _active_goals() -> list[dict]:
    """Every goal that's neither completed nor cancelled, newest-first
    - same filter frontend-legacy/view_data/goal_overview.py already
    established (build_goal_overview()), not a new convention."""
    latest = get_latest_for_all_goals()
    active = [r for r in latest if not r.get("completed") and not r.get("cancelled")]
    active.sort(key=created_at_key, reverse=True)
    return active


def _completed_goals() -> list[dict]:
    """Every goal marked completed - cancelled goals are deliberately
    excluded, same reasoning as frontend-legacy's build_goal_overview():
    cancelled is its own status, not a kind of completed. Oldest-first,
    also matching that precedent (unlike _active_goals())."""
    latest = get_latest_for_all_goals()
    completed = [r for r in latest if r.get("completed")]
    completed.sort(key=created_at_key)
    return completed


# The plan fields worth showing in a history entry, in a fixed,
# readable order - not every key in the raw plan dict (e.g. `steps`
# renders as a count, not the full nested tree; History is a log to
# scan, not another place to render the live plan tree Active already
# shows).
_HISTORY_PLAN_FIELDS = (
    "clarification", "suggested_action", "suggested_duration",
    "year", "month", "week", "today", "hour", "minute", "now",
)


def _history_view(record: dict) -> dict:
    """One raw history entry - deliberately closer to
    frontend-legacy/templates/_plan_entry.html's plain key:value dump
    than to _goal_view()'s curated, UI-ready shape. History is the
    unfiltered log (every record ever saved, not just the latest per
    goal - see load_history()), so it shows what was actually saved,
    not a live status."""
    plan = record.get("plan") or {}
    steps = plan.get("steps")
    return {
        "id": record["id"],
        "goal_id": record["goal_id"],
        "goal": record["goal"],
        "duration": record.get("duration"),
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "feedback": record.get("feedback"),
        "created_at": record["created_at"],
        "plan": {key: plan.get(key) for key in _HISTORY_PLAN_FIELDS if plan.get(key)},
        "step_count": len(steps) if steps else 0,
    }


def _session_view() -> dict:
    """{goal_id, goal} - goal_id mirrors cli.py's Session.
    current_goal_id (None if the free-conversation path hasn't touched
    a goal yet this process); goal is that record's own text, looked
    up fresh each call rather than cached, same reasoning as every
    other _*_view() here. Deliberately just this process's live
    pointer, not the persisted Session record itself - see
    _session_log_view() below for that."""
    goal_id = session.current_goal_id
    if goal_id is None:
        return {"goal_id": None, "goal": None}
    latest = get_latest_for_goal(goal_id)
    return {"goal_id": goal_id, "goal": latest["goal"] if latest else None}


def _session_goal_event(record: dict) -> dict:
    """One line in a Session's derived log for a goal/plan record -
    lighter than _history_view()'s full shape, just enough to render a
    timeline entry. `feedback` is None for the record that created the
    goal (see data_persistence.save_plan()'s own docstring), otherwise
    the feedback that produced this particular replan - the UI reads
    that distinction to label the event "created" vs. the feedback
    text itself."""
    return {
        "goal_id": record["goal_id"],
        "goal": record["goal"],
        "feedback": record.get("feedback"),
        "created_at": record["created_at"],
    }


def _session_vision_event(vision: dict) -> dict:
    """One line in a Session's derived log for a Vision - only ever a
    creation event, since archiving isn't timestamped yet (see
    data_persistence.archive_vision()'s own docstring)."""
    return {
        "vision_id": vision["id"],
        "text": vision["text"],
        "created_at": vision["created_at"],
    }


def _session_log_view(record: dict, window_end: str | None) -> dict:
    """A persisted Session record plus everything that happened during
    it - derived at read time, not logged by any mutating route: every
    load_history()/load_visions() entry whose `created_at` falls
    inside [started_at, window_end or now) belongs to this Session,
    because nothing else currently could have created it.

    `window_end` is NOT simply `record["ended_at"]` (always None today
    - see data_persistence.start_session()) - it's computed by the
    do_GET route below as the next Session's own `started_at`, since a
    later Session starting is the only signal available yet that an
    earlier one stopped being "the current one". Without this, every
    Session before the most recent would look open forever and match
    every event that happened after it, not just its own - reproduced
    and fixed within this same 2026-09-12 session. Reported back as
    this view's own `ended_at`: a best-available boundary, not
    necessarily a moment a real shutdown was ever observed. Only the
    single most recent Session (no successor) gets `window_end=None`,
    genuinely still open.

    Both event lists are sorted oldest-first, independent of
    load_history()'s own newest-first order, so the Session page reads
    as a timeline."""
    start = record["started_at"]
    end = window_end
    goal_events = sorted(
        (
            _session_goal_event(r) for r in load_history()
            if start <= r["created_at"] and (end is None or r["created_at"] < end)
        ),
        key=lambda e: e["created_at"],
    )
    vision_events = sorted(
        (
            _session_vision_event(v) for v in load_visions()
            if start <= v["created_at"] and (end is None or v["created_at"] < end)
        ),
        key=lambda e: e["created_at"],
    )
    return {
        "id": record["id"],
        "started_at": start,
        "ended_at": end,
        "goal_events": goal_events,
        "vision_events": vision_events,
    }


def _vision_view(vision: dict) -> dict:
    """{id, text, archived, created_at} - load_visions()'s own record
    shape already has exactly these fields, `archived` just isn't
    guaranteed present (see data_persistence.archive_vision(), only
    ever set once true) - normalized to always-present here so the UI
    doesn't need to know that."""
    return {
        "id": vision["id"],
        "text": vision["text"],
        "archived": bool(vision.get("archived")),
        "created_at": vision["created_at"],
    }


# 3. HTTP handler


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/goals":
            self._send_json([_goal_view(r) for r in _active_goals()])
            return
        if self.path == "/api/goals/completed":
            self._send_json([_goal_view(r) for r in _completed_goals()])
            return
        if self.path == "/api/history":
            self._send_json([_history_view(r) for r in reversed(load_history())])
            return
        if self.path == "/api/visions":
            self._send_json([_vision_view(v) for v in load_visions()])
            return
        if self.path == "/api/session":
            self._send_json(_session_view())
            return
        if self.path == "/api/sessions":
            # Oldest-first while computing each one's window_end (the
            # next Session's started_at, see _session_log_view()'s own
            # docstring for why), reversed only for the final response
            # so the page itself still reads newest-first, same
            # convention as /api/history.
            by_start = sorted(load_sessions(), key=lambda s: s["started_at"])
            views = [
                _session_log_view(
                    record,
                    record.get("ended_at") or (by_start[i + 1]["started_at"] if i + 1 < len(by_start) else None),
                )
                for i, record in enumerate(by_start)
            ]
            self._send_json(list(reversed(views)))
            return
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
        if self.path == "/api/message":
            self._handle_message()
            return
        if self.path == "/api/goals":
            self._handle_create_goal()
            return
        if self.path == "/api/visions":
            self._handle_create_vision()
            return
        if self.path == "/api/session":
            self._handle_set_session()
            return
        feedback_match = _FEEDBACK_PATH_RE.match(self.path)
        if feedback_match:
            self._handle_goal_feedback(int(feedback_match.group(1)))
            return
        cancel_match = _CANCEL_PATH_RE.match(self.path)
        if cancel_match:
            self._handle_cancel_goal(int(cancel_match.group(1)))
            return
        goal_vision_match = _GOAL_VISION_PATH_RE.match(self.path)
        if goal_vision_match:
            self._handle_set_goal_vision(int(goal_vision_match.group(1)))
            return
        archive_match = _VISION_ARCHIVE_PATH_RE.match(self.path)
        if archive_match:
            self._handle_archive_vision(int(archive_match.group(1)))
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

    def _handle_message(self) -> None:
        user_text = self._read_text_body()
        if user_text is None:
            return
        try:
            result = process_turn(session, user_text)
        except Exception as e:  # transport must not crash on one bad turn
            # Same reasoning as cli.py's own fallback: a friendly,
            # deterministic line, not the raw exception text, standing
            # in as "the agent's reply" - reasoning.model_client.
            # call_with_retry already absorbs the model-shape hiccups
            # this is most likely to be. Printed server-side (not to
            # the client) for whoever is actually debugging this run.
            print(f"(debug: {e})")
            result = {
                "understanding": None, "capability": None, "surface": None,
                "node": None, "goal_id": None,
                "reply": "That took longer than expected - try again in a moment.",
            }
        self._send_json(result)

    def _handle_create_goal(self) -> None:
        text = self._read_text_body()
        if text is None:
            return
        try:
            record = create_goal(text, "", "")
        except Exception as e:  # same reasoning as _handle_message()
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(_goal_view(record))

    def _handle_goal_feedback(self, goal_id: int) -> None:
        note = self._read_text_body()
        if note is None:
            return
        latest = get_latest_for_goal(goal_id)
        if latest is None:
            self.send_error(404, "no such goal")
            return
        try:
            record = apply_feedback(latest, note)
        except Exception as e:  # same reasoning as _handle_message()
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(_goal_view(record))

    def _handle_cancel_goal(self, goal_id: int) -> None:
        # No request body - same reasoning as _handle_archive_vision():
        # the goal is already named by id in the path. planner.
        # cancel_goal() is a pure state transition (no model call), so
        # there's nothing to retry here, unlike _handle_goal_feedback().
        record = cancel_goal(goal_id)
        if record is None:
            self.send_error(404, "no such goal, or already completed")
            return
        self._send_json(_goal_view(record))

    def _handle_set_goal_vision(self, goal_id: int) -> None:
        # Body is {"vision_id": <int>} or {"vision_id": null} to remove
        # the link - not {"text": ...} like every other POST route
        # here, so this doesn't go through _read_text_body(). No model
        # call, same as _handle_cancel_goal() - a pure state transition.
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        raw_vision_id = payload_in.get("vision_id")
        vision_id = int(raw_vision_id) if raw_vision_id is not None else None
        record = set_goal_vision(goal_id, vision_id)
        if record is None:
            self.send_error(404, "no such goal or vision, or an unanswered clarification blocks this")
            return
        self._send_json(_goal_view(record))

    def _handle_set_session(self) -> None:
        # Body is {"goal_id": <int>} or {"goal_id": null} to clear it -
        # not {"text": ...} like every other POST route here, so this
        # doesn't go through _read_text_body(). No model call, same
        # reasoning as _handle_cancel_goal() - a pure state write onto
        # the module-level `session` object, nothing saved to disk.
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        raw_goal_id = payload_in.get("goal_id")
        if raw_goal_id is None:
            session.current_goal_id = None
            self._send_json(_session_view())
            return
        goal_id = int(raw_goal_id)
        if get_latest_for_goal(goal_id) is None:
            self.send_error(404, "no such goal")
            return
        session.current_goal_id = goal_id
        self._send_json(_session_view())

    def _handle_create_vision(self) -> None:
        text = self._read_text_body()
        if text is None:
            return
        vision = save_vision(text)  # pure append, no model call - nothing to retry
        self._send_json(_vision_view(vision))

    def _handle_archive_vision(self, vision_id: int) -> None:
        # No request body to read - archiving names the Vision by id
        # in the path, same as feedback names the Goal by id.
        vision = archive_vision(vision_id)
        if vision is None:
            self.send_error(404, "no such vision")
            return
        self._send_json(_vision_view(vision))

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass  # keep the terminal for the conversation, not HTTP access logs


# 4. Entry point

if __name__ == "__main__":
    print(f"web prototype - http://localhost:{PORT}/")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
