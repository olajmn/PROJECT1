"""
The demo-mode check in front of every request (docs/demo.md).
requests_from_browser.Handler calls guard() first; when it
returns True, the request has been answered here (login, logout, 401,
403, 413, 429, or a redirect to the login page) and Handler does
nothing more. When it returns False, storage has been pointed at the
visitor's sandbox (backend/storage/sandboxes.py), or at nothing for a
request without a session, which never reaches storage.
"""

# Contents
#  1. State
#      - _BLOCKED, sessions, limits; sandboxes cleared at start
#
#  2. The check
#      - guard()
#
#  3. Login and logout
#      - _login(), _logout()
#
#  4. Helpers
#      - client_ip(), _token(), _content_length(), _cookie(), _send_json()

import hmac
import json
import re
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler

from backend.api.demo import settings
from backend.api.demo.limits import RateLimit
from backend.api.demo.sessions import Session, Sessions
from backend.storage import sandboxes


# ============================================================
# 1. State
# ============================================================

COOKIE = "demo_session"
LOGIN_PAGE = "/login.html"

_CHAT = re.compile(r"^/api/projects/\d+/chat$")

# These reach the server's own file system and desktop, not the
# visitor's data: folder_tree() lists any server path it is given, and
# choose_folder() runs osascript.
_BLOCKED = (
    re.compile(r"^/api/projects/\d+/map/folder$"),
    re.compile(r"^/api/choose-folder$"),
)


def _remove_sandbox(session: Session) -> None:
    sandboxes.remove(session.sandbox)


sessions = Sessions(
    settings.IDLE_SECONDS,
    settings.MAX_SECONDS,
    settings.MAX_SESSIONS,
    on_end=_remove_sandbox,
)
login_failures = RateLimit(*settings.LOGIN_FAILURES_PER_IP)
talk_per_session = RateLimit(*settings.TALK_PER_SESSION)
talk_per_ip = RateLimit(*settings.TALK_PER_IP)
talk_per_day = RateLimit(*settings.TALK_PER_DAY)

if settings.ENABLED:
    # Sessions do not survive a restart, so neither do their sandboxes.
    sandboxes.clear_all()


# ============================================================
# 2. The check
# ============================================================

def guard(handler: BaseHTTPRequestHandler, method: str) -> bool:
    """True when the request was answered here; False lets Handler
    answer it as usual."""
    path = handler.path.split("?", 1)[0]
    # Until a session is found, storage points at no sandbox; this thread
    # may have answered another visitor before.
    sandboxes.use(None)
    if method == "POST" and path == "/api/login":
        _login(handler)
        return True
    if method == "POST" and path == "/api/logout":
        _logout(handler)
        return True

    session = sessions.get(_token(handler))
    if session is None:
        if path.startswith("/api/"):
            handler.send_error(401, "Log in to continue.")
            return True
        if path == "/" or (path.endswith(".html") and path != LOGIN_PAGE):
            handler.send_response(303)
            handler.send_header("Location", LOGIN_PAGE)
            handler.send_header("Content-Length", "0")
            handler.end_headers()
            return True
        # The login page and the scripts and styles every page loads.
        return False

    if session.sandbox is None:
        # Never fall back to data/ for a logged-in visitor.
        handler.send_error(503, "The demo is not ready. Log in again.")
        return True
    sandboxes.use(session.sandbox)
    if method != "POST":
        return False
    if any(pattern.match(path) for pattern in _BLOCKED):
        handler.send_error(403, "Not available in the demo.")
        return True
    length = _content_length(handler)
    if length is None:
        handler.send_error(400, "invalid Content-Length")
        return True
    is_chat = bool(_CHAT.match(path))
    if length > (settings.CHAT_BODY_MAX_BYTES if is_chat else settings.BODY_MAX_BYTES):
        handler.send_error(413, "Too long for the demo.")
        return True
    if is_chat and not (
        talk_per_session.allow(session.token)
        and talk_per_ip.allow(client_ip(handler))
        and talk_per_day.allow("all")
    ):
        handler.send_error(429, "Too many messages for the demo. Try again in a minute.")
        return True
    return False


# ============================================================
# 3. Login and logout
# ============================================================

def _login(handler: BaseHTTPRequestHandler) -> None:
    ip = client_ip(handler)
    if login_failures.full(ip):
        handler.send_error(429, "Too many wrong passwords. Try again in a few minutes.")
        return
    length = _content_length(handler)
    if length is None or length > settings.LOGIN_BODY_MAX_BYTES:
        handler.send_error(400, "invalid login request")
        return
    try:
        body = json.loads(handler.rfile.read(length) or b"{}")
    except json.JSONDecodeError:
        handler.send_error(400, "invalid login request")
        return
    password = str(body.get("password") or "") if isinstance(body, dict) else ""
    if not hmac.compare_digest(password.encode(), settings.PASSWORD.encode()):
        login_failures.allow(ip)
        handler.send_error(401, "Wrong password.")
        return
    session = sessions.create()
    if session is None:
        handler.send_error(503, "The demo is full right now. Try again later.")
        return
    try:
        session.sandbox = sandboxes.create()
    except OSError as e:
        print(f"(debug: sandbox not created: {type(e).__name__})")
        sessions.end(session.token)
        handler.send_error(503, "The demo is not available right now. Try again later.")
        return
    _send_json(handler, {"ok": True}, _cookie(session.token, settings.MAX_SECONDS))


def _logout(handler: BaseHTTPRequestHandler) -> None:
    sessions.end(_token(handler))
    _send_json(handler, {"ok": True}, _cookie("", 0))


# ============================================================
# 4. Helpers
# ============================================================

def client_ip(handler: BaseHTTPRequestHandler) -> str:
    """The visitor's IP: the proxy's header when one is configured,
    otherwise the connection's own address."""
    if settings.CLIENT_IP_HEADER:
        forwarded = (handler.headers.get(settings.CLIENT_IP_HEADER) or "").strip()
        if forwarded:
            return forwarded
    return handler.client_address[0]


def _token(handler: BaseHTTPRequestHandler) -> str | None:
    cookie = SimpleCookie()
    try:
        cookie.load(handler.headers.get("Cookie") or "")
    except CookieError:
        return None
    morsel = cookie.get(COOKIE)
    return morsel.value if morsel else None


def _content_length(handler: BaseHTTPRequestHandler) -> int | None:
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        return None
    return length if length >= 0 else None


def _cookie(token: str, max_age: int) -> str:
    parts = [f"{COOKIE}={token}", "HttpOnly", "SameSite=Strict", "Path=/", f"Max-Age={max_age}"]
    if settings.SECURE_COOKIE:
        parts.append("Secure")
    return "; ".join(parts)


def _send_json(handler: BaseHTTPRequestHandler, payload: dict, cookie: str) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Set-Cookie", cookie)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
