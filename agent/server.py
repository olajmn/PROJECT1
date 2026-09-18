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
  documents for the free-conversation path. POST /api/goals/<id>/feedback
  is the exception on this path: it runs planning/chat/turn.py (Describe in
  context -> route_note -> Voice), still keyed by the id in the URL, so
  it cannot pick the wrong goal. Other known-context routes stay
  silent of Node 1 - see manifestation.py's surface_text()/
  to_planning_node(), already deterministic and already what
  ui/active.html's plan tree shows directly.
- GET/POST /api/chat-focus - the manual bridge between the two paths
  above: reads or overwrites the free-conversation `session`'s own
  `chat_focus.goal_id` - which goal, if any, the chat is currently
  "focused" on - otherwise invisible and unsettable from any page.
  Lets e.g. Active point the chat at a specific existing goal instead
  of only ever guessing - still doesn't address § 5's mid-conversation
  topic-switch defect itself, only gives an explicit, visible starting
  point. Named "chat focus", not "session", to keep it distinct from
  the persisted Session below - `cli.py`'s `Session` object owns a
  `ChatFocus` (its `chat_focus` attribute) rather than flattening
  `goal_id` onto itself, so the two stay structurally separate too,
  not just separately named (see _chat_focus_view()'s own docstring).
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
#        _VISION_ARCHIVE_PATH_RE, _ZOOM_PATH_RE
#      - session (process-wide, /api/message only)
#      - tree, tree_duration, tree_zoomed (process-wide, Steps page)
#      - _mint_step_id()
#
#  2. View builders
#      - _goal_view()
#      - _active_goals()
#      - _completed_goals()
#      - _HISTORY_PLAN_FIELDS
#      - _history_view()
#      - _chat_focus_view()
#      - _session_goal_event()
#      - _session_vision_event()
#      - _session_log_view()
#      - _vision_view()
#      - _step_view()
#      - _tree_view()
#      - _ancestor_labels()
#
#  3. HTTP handler
#      - Handler
#          - do_GET()
#          - do_POST()
#          - _read_text_body()
#          - _handle_message()
#          - _handle_create_tree()
#          - _handle_zoom_step()
#          - _handle_create_goal()
#          - _handle_goal_feedback()
#          - _handle_cancel_goal()
#          - _handle_set_goal_vision()
#          - _handle_set_chat_focus()
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
from backend.foundation.time import extract_duration_phrase
from backend.infrastructure.data_persistence import load_history, load_sessions, load_visions, save_vision
from backend.planning.chat.thread import thread_for
from backend.planning.chat.turn import take_turn
from backend.planning.goal.lifecycle import cancel_goal, create_goal
from backend.planning.goal.resolver import created_at_key, get_latest_for_all_goals, get_latest_for_goal
from backend.planning.plan.planner import archive_vision, set_goal_vision
from backend.planning.plan.progression_zoom import (
    add_progression_bead,
    remove_progression_bead,
    zoom_progression_step,
)
from backend.planning.plan.step import Step
from backend.planning.plan.zoom import zoom_into

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
_GOAL_ZOOM_PATH_RE = re.compile(r"^/api/goals/(\d+)/zoom/(p\d+)$")
_GOAL_PROGRESSION_PATH_RE = re.compile(r"^/api/goals/(\d+)/progression$")
_GOAL_PROGRESSION_REMOVE_RE = re.compile(
    r"^/api/goals/(\d+)/progression/(p\d+)/remove$",
)
_VISION_ARCHIVE_PATH_RE = re.compile(r"^/api/visions/(\d+)/archive$")
_ZOOM_PATH_RE = re.compile(r"^/api/tree/(s\d+)/zoom$")

session = Session()  # process-wide - see module docstring, /api/message only

# The Steps page's scratch tree (§ 5 below). In memory, one at a
# time, lost on restart, and deliberately NOT written through
# data_persistence: docs/planning-model.md § Decomposition / zoom
# leaves whether zoomed content is persisted explicitly undecided, so
# this page exists to look at the shape before that call is made. It
# is a workbench for the recursive Step model, not a second way to
# create a real Goal.
tree: Step | None = None
tree_duration = ""
# Which steps have actually been through zoom_into(). A step with no
# children means "not zoomed yet" or "zoomed, and the verdict was
# that an Action can already be projected from it" - opposite
# meanings for the UI, and nothing in Step itself distinguishes them.
tree_zoomed: set[str] = set()
_step_counter = 0


def _mint_step_id() -> str:
    global _step_counter
    _step_counter += 1
    return f"s{_step_counter}"

# 2. View builders


def _goal_view(record: dict, reply: str | None = None) -> dict:
    """The one shape every /api/goals response uses for a single goal
    - record fields a UI actually needs (identity, display text,
    completion) plus the same manifestation.py translation
    /api/message already relies on, so ui/active.ts and ui/src/main.ts
    render an identical plan tree from an identical shape. `thread` is
    the goal-scoped chat reconstructed from this goal's history;
    `reply` is Voice's wording for the turn just taken, or null on a
    plain GET."""
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
        "thread": thread_for(record["goal_id"], reply),
        "reply": reply,
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


def _chat_focus_view() -> dict:
    """{goal_id, goal} - which goal, if any, the free-conversation path
    is currently "focused" on: goal_id mirrors cli.py's Session.
    chat_focus.goal_id (None if the chat hasn't touched a goal yet
    this process); goal is that record's own text, looked up fresh
    each call rather than cached, same reasoning as every other
    _*_view() here.

    Named "chat focus" rather than "session" - added 2026-09-12,
    renamed from _session_view() the same day - specifically to keep
    it distinct from the persisted Session record (_session_log_view()
    below): `cli.py`'s `Session` object owns a `ChatFocus` (this) and
    separately mirrors a persisted Session record (`id`/`started_at`,
    that) as two structurally separate things, not one flattened onto
    the other. This function is deliberately just the live pointer,
    never the persisted Session record itself."""
    goal_id = session.chat_focus.goal_id
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


def _step_view(step: Step) -> dict:
    """A Step as the Steps page needs it: the PlanningNode fields the
    UI's tree renderer already understands, plus `zoomed` (see
    tree_zoomed) so a childless step can say whether it is unexplored
    or settled."""
    return {
        "id": step.id,
        "label": step.label,
        "status": "done" if step.resolved else "open",
        "zoomed": step.id in tree_zoomed,
        "children": [_step_view(child) for child in step.children],
    }


def _tree_view() -> dict:
    return {"duration": tree_duration, "root": _step_view(tree) if tree else None}


def _ancestor_labels(root: Step, step_id: str) -> list[str] | None:
    """The labels on the path from `root` down to (not including)
    `step_id`, outermost first - what zoom_into() wants as context.
    None if `step_id` isn't in this tree. Recomputed by walking rather
    than stored as parent links on Step, which would make the tree
    cyclic and so unserializable (see step.py's own docstring)."""
    if root.id == step_id:
        return []
    for child in root.children:
        below = _ancestor_labels(child, step_id)
        if below is not None:
            return [root.label, *below]
    return None


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
        if self.path == "/api/chat-focus":
            self._send_json(_chat_focus_view())
            return
        if self.path == "/api/tree":
            # So a reload (or coming back from another page) shows the
            # tree that's already there instead of a blank form -
            # every zoom costs two model calls, which is far too
            # expensive to redo just because the page was left.
            self._send_json(_tree_view())
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
        # Project workspace is the product home (prototype); free chat
        # remains at /index.html.
        requested = "projects.html" if self.path == "/" else self.path.lstrip("/")
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
        if self.path == "/api/chat-focus":
            self._handle_set_chat_focus()
            return
        if self.path == "/api/tree":
            self._handle_create_tree()
            return
        zoom_match = _ZOOM_PATH_RE.match(self.path)
        if zoom_match:
            self._handle_zoom_step(zoom_match.group(1))
            return
        goal_zoom_match = _GOAL_ZOOM_PATH_RE.match(self.path)
        if goal_zoom_match:
            self._handle_goal_zoom(
                int(goal_zoom_match.group(1)), goal_zoom_match.group(2),
            )
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
            result = process_turn(session.chat_focus, user_text)
        except Exception as e:  # transport must not crash on one bad turn
            # Same reasoning as cli.py's own fallback: a friendly,
            # deterministic line, not the raw exception text, standing
            # in as "the agent's reply" - model.client.call_with_retry
            # already absorbs the model-shape hiccups
            # this is most likely to be. Printed server-side (not to
            # the client) for whoever is actually debugging this run.
            print(f"(debug: {e})")
            result = {
                "understanding": None, "capability": None, "surface": None,
                "node": None, "goal_id": None,
                "reply": "That took longer than expected - try again in a moment.",
            }
        self._send_json(result)

    def _handle_create_tree(self) -> None:
        """Start a fresh scratch tree from typed text: the text
        becomes the root step, and the tree starts unexpanded - even
        the root's first level is a zoom the user asks for, so the
        page shows on-demand depth from the very first click rather
        than pre-expanding one level for free.

        Rejects text with no recognizable time phrase in it, before
        any model call, exactly as create_goal() does - a goal
        is not plannable from its wording alone here (see zoom.py).
        The 422 says which half is missing; the real Set Goal flow
        asks a clarification question instead, which this workbench
        deliberately doesn't reimplement."""
        global tree, tree_duration, tree_zoomed
        text = self._read_text_body()
        if text is None:
            return
        duration = extract_duration_phrase(text)
        if duration is None:
            self.send_error(422, "no timeframe recognized - say when, e.g. 'in 18 months'")
            return
        tree = Step(id=_mint_step_id(), label=text)
        tree_duration = duration
        tree_zoomed = set()
        self._send_json(_tree_view())

    def _handle_zoom_step(self, step_id: str) -> None:
        """Raise the resolution of one step, in place, and return the
        WHOLE tree rather than just the new children - the tree is
        small, and one shape for every response keeps the page from
        having to splice a subtree into what it already has.

        Re-zooming a step that already has children replaces them:
        the step keeps its identity while the understanding underneath
        it changes, which is the point of § Decomposition / zoom."""
        if tree is None:
            self.send_error(409, "no tree yet")
            return
        step = tree.find(step_id)
        ancestors = _ancestor_labels(tree, step_id)
        if step is None or ancestors is None:
            self.send_error(404, "no such step")
            return
        try:
            labels = zoom_into(step.label, ancestors, tree_duration)
        except Exception as e:  # same reasoning as _handle_message()
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        step.children = [Step(id=_mint_step_id(), label=label) for label in labels]
        tree_zoomed.add(step_id)
        self._send_json(_tree_view())

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

    def _handle_goal_zoom(self, goal_id: int, step_id: str) -> None:
        """One level deeper under a Step in plan.progression — persists
        on the Goal so Active's plan box grows. Steps workbench
        (/api/tree) is unchanged."""
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
        self._send_json(_goal_view(record))

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
        self._send_json(_goal_view(record))

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
        self._send_json(_goal_view(record))

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
        except Exception as e:  # same reasoning as _handle_message()
            print(f"(debug: {e})")
            self.send_error(503, "that took longer than expected - try again in a moment")
            return
        self._send_json(_goal_view(result["record"], reply=result["reply"]))

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

    def _handle_set_chat_focus(self) -> None:
        # Body is {"goal_id": <int>} or {"goal_id": null} to clear it -
        # not {"text": ...} like every other POST route here, so this
        # doesn't go through _read_text_body(). No model call, same
        # reasoning as _handle_cancel_goal() - a pure state write onto
        # the module-level `session` object's own chat_focus.goal_id,
        # nothing saved to disk.
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload_in = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return
        raw_goal_id = payload_in.get("goal_id")
        if raw_goal_id is None:
            session.chat_focus.goal_id = None
            self._send_json(_chat_focus_view())
            return
        goal_id = int(raw_goal_id)
        if get_latest_for_goal(goal_id) is None:
            self.send_error(404, "no such goal")
            return
        session.chat_focus.goal_id = goal_id
        self._send_json(_chat_focus_view())

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
