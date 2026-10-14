"""Checks for demo mode: sessions, rate limits, guard(), and sandboxes -
a fake request, a fake clock, and temporary folders; no server, no real
data, no model. Run from app/:

    .venv/bin/python -m backend.api.demo.test_demo
"""

import io
import json
import tempfile
from pathlib import Path
from unittest import mock

from backend.api.demo import check as g
from backend.api.demo import settings
from backend.api.demo.limits import RateLimit
from backend.api.demo.sessions import Sessions
from backend.project.panes.create.lifecycle import create_project
from backend.project.panes.create.resolver import get_latest_for_all_projects
from backend.storage import paths, sandboxes
from backend.storage.accounts_persistence import load_accounts, save_account


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeRequest:
    """Just what guard() touches on a BaseHTTPRequestHandler."""

    def __init__(self, path, body=b"", cookie=None, ip="1.2.3.4", headers=None):
        self.path = path
        self.headers = {"Content-Length": str(len(body))}
        if cookie:
            self.headers["Cookie"] = f"{g.COOKIE}={cookie}"
        self.headers.update(headers or {})
        self.client_address = (ip, 50000)
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = None
        self.message = None
        self.sent_headers = {}

    def send_error(self, code, message=None):
        self.status, self.message = code, message

    def send_response(self, code):
        self.status = code

    def send_header(self, name, value):
        self.sent_headers[name] = value

    def end_headers(self):
        pass


def fresh_state(clock):
    """New sessions and limits on the fake clock, with small limits."""
    g.sessions = Sessions(idle=30 * 60, max_age=8 * 60 * 60, limit=2, clock=clock,
                          on_end=g._remove_sandbox)
    g.login_failures = RateLimit(3, 60, clock)
    g.talk_per_session = RateLimit(2, 60, clock)
    g.talk_per_ip = RateLimit(10, 60, clock)
    g.talk_per_day = RateLimit(100, 24 * 60 * 60, clock)


def login(password="secret", ip="1.2.3.4"):
    request = FakeRequest("/api/login", json.dumps({"password": password}).encode(), ip=ip)
    assert g.guard(request, "POST") is True
    cookie = request.sent_headers.get("Set-Cookie", "")
    token = cookie.split(";")[0].split("=", 1)[1] if request.status == 200 else None
    return request, token


def check_sessions_and_limits() -> None:
    clock = Clock()
    sessions = Sessions(idle=10, max_age=100, limit=1, clock=clock)
    first = sessions.create()
    assert first is not None and sessions.create() is None  # at the limit
    clock.now += 9
    assert sessions.get(first.token) is first  # used: idle timer restarts
    clock.now += 9
    assert sessions.get(first.token) is first
    clock.now += 11
    assert sessions.get(first.token) is None  # idle too long

    second = sessions.create()
    for _ in range(12):  # keep it busy past max_age
        clock.now += 9
        sessions.get(second.token)
    assert sessions.get(second.token) is None  # older than max_age
    third = sessions.create()
    sessions.end(third.token)
    assert sessions.get(third.token) is None
    assert sessions.get(None) is None and sessions.get("") is None

    limit = RateLimit(2, 60, clock)
    assert limit.allow("a") and limit.allow("a") and not limit.allow("a")
    assert limit.allow("b")  # per key
    clock.now += 60
    assert limit.allow("a")  # window passed


def check_guard() -> None:
    clock = Clock()
    fresh_state(clock)
    with mock.patch.object(settings, "PASSWORD", "secret"), \
         mock.patch.object(settings, "SECURE_COOKIE", True):
        # No session: API is 401, pages go to the login page, assets load.
        request = FakeRequest("/api/projects")
        assert g.guard(request, "GET") and request.status == 401
        for page in ("/", "/settings/logs.html"):
            request = FakeRequest(page)
            assert g.guard(request, "GET") and request.status == 303
            assert request.sent_headers["Location"] == "/login.html"
        for public in ("/login.html", "/dist/demo/login.js", "/css/style.css"):
            assert g.guard(FakeRequest(public), "GET") is False
        request = FakeRequest("/api/projects/1/map", b"{}")
        assert g.guard(request, "POST") and request.status == 401

        # Wrong password, then right one; the cookie is locked down.
        request, token = login("wrong")
        assert request.status == 401 and token is None
        request, token = login()
        assert request.status == 200 and token
        cookie = request.sent_headers["Set-Cookie"]
        for part in ("HttpOnly", "SameSite=Strict", "Path=/", "Secure",
                     f"Max-Age={settings.MAX_SECONDS}"):
            assert part in cookie, part

        # With the session, Handler answers.
        assert g.guard(FakeRequest("/api/projects", cookie=token), "GET") is False
        assert g.guard(FakeRequest("/", cookie=token), "GET") is False
        assert g.guard(FakeRequest("/api/log?offset=50", cookie=token), "GET") is False
        assert g.guard(FakeRequest("/api/projects/1/map", b"{}", cookie=token), "POST") is False
        assert g.guard(FakeRequest("/api/projects/1/delete", b"", cookie=token), "POST") is False

        # The two routes that reach the server itself are blocked.
        for blocked in ("/api/projects/1/map/folder", "/api/choose-folder"):
            request = FakeRequest(blocked, b'{"path": "/"}', cookie=token)
            assert g.guard(request, "POST") and request.status == 403

        # Size limits: general body, and the smaller chat body.
        big = b"x" * (settings.BODY_MAX_BYTES + 1)
        request = FakeRequest("/api/projects/1/map/import", big, cookie=token)
        assert g.guard(request, "POST") and request.status == 413
        long_chat = b"x" * (settings.CHAT_BODY_MAX_BYTES + 1)
        request = FakeRequest("/api/projects/1/chat", long_chat, cookie=token)
        assert g.guard(request, "POST") and request.status == 413
        request = FakeRequest("/api/projects/1/map", b"{}", cookie=token,
                              headers={"Content-Length": "abc"})
        assert g.guard(request, "POST") and request.status == 400

        # Talk: 2 a minute per session here, then 429; a minute later, fine.
        chat = b'{"text": "hi"}'
        for _ in range(2):
            assert g.guard(FakeRequest("/api/projects/1/chat", chat, cookie=token), "POST") is False
        request = FakeRequest("/api/projects/1/chat", chat, cookie=token)
        assert g.guard(request, "POST") and request.status == 429
        clock.now += 60
        assert g.guard(FakeRequest("/api/projects/1/chat", chat, cookie=token), "POST") is False

        # Session cap: 2 here.
        _, second = login(ip="5.6.7.8")
        assert second
        request, third = login(ip="5.6.7.8")
        assert request.status == 503 and third is None

        # Logout ends the session and clears the cookie.
        request = FakeRequest("/api/logout", b"", cookie=token)
        assert g.guard(request, "POST") and request.status == 200
        assert "Max-Age=0" in request.sent_headers["Set-Cookie"]
        request = FakeRequest("/api/projects", cookie=token)
        assert g.guard(request, "GET") and request.status == 401

        # Idle timeout: 30 minutes without a request.
        clock.now += 30 * 60 + 1
        request = FakeRequest("/api/projects", cookie=second)
        assert g.guard(request, "GET") and request.status == 401

        # Wrong passwords: 3 a minute per IP here. Right ones do not count.
        g.sessions.end(second)
        for _ in range(5):
            request, token_ok = login(ip="9.9.9.9")
            assert request.status == 200
            g.sessions.end(token_ok)
        for _ in range(3):
            request, _ = login("wrong", ip="9.9.9.9")
            assert request.status == 401
        request, _ = login(ip="9.9.9.9")
        assert request.status == 429
        clock.now += 60
        request, token_ok = login(ip="9.9.9.9")
        assert request.status == 200
        g.sessions.end(token_ok)

        # A forged client-IP header counts only when a proxy header is set.
        spoof = FakeRequest("/x", headers={"Fly-Client-IP": "7.7.7.7"})
        assert g.client_ip(spoof) == "1.2.3.4"
        with mock.patch.object(settings, "CLIENT_IP_HEADER", "Fly-Client-IP"):
            assert g.client_ip(spoof) == "7.7.7.7"

    # Without SECURE_COOKIE (local http only) the flag is left off.
    fresh_state(clock)
    with mock.patch.object(settings, "PASSWORD", "secret"), \
         mock.patch.object(settings, "SECURE_COOKIE", False):
        request, _ = login()
        assert "Secure" not in request.sent_headers["Set-Cookie"]


def check_sandboxes() -> None:
    clock = Clock()
    fresh_state(clock)
    with mock.patch.object(settings, "PASSWORD", "secret"), \
         mock.patch.object(settings, "SECURE_COOKIE", True):
        # A login gets a copy of the seed; ending the session removes it.
        _, a = login()
        _, b = login(ip="5.6.7.8")
        box_a = sandboxes.ROOT / g.sessions.get(a).sandbox
        box_b = sandboxes.ROOT / g.sessions.get(b).sandbox
        assert box_a != box_b
        assert (box_a / "accounts.json").read_text() == '[{"id": 1, "text": "Demo"}]'

        # Storage follows the request's sandbox: what A does, B never sees.
        assert g.guard(FakeRequest("/api/projects", cookie=a), "GET") is False
        assert paths.data_dir() == box_a
        create_project("Only in A", "1")
        save_account("Second in A")
        assert [r["name"] for r in get_latest_for_all_projects()] == ["Only in A"]
        assert len(load_accounts()) == 2

        assert g.guard(FakeRequest("/api/projects", cookie=b), "GET") is False
        assert paths.data_dir() == box_b
        assert get_latest_for_all_projects() == []
        assert len(load_accounts()) == 1

        # No session: storage points at no sandbox (and the API is 401).
        request = FakeRequest("/api/projects")
        assert g.guard(request, "GET") and request.status == 401
        assert sandboxes.current() is None

        # Logout and idle expiry both delete the folder.
        g.guard(FakeRequest("/api/logout", b"", cookie=a), "POST")
        assert not box_a.exists()
        clock.now += 30 * 60 + 1
        g.sessions.get("none")  # any lookup sweeps expired sessions
        assert not box_b.exists()

        # A new login starts from the seed again.
        _, c = login(ip="9.9.9.9")
        g.guard(FakeRequest("/api/projects", cookie=c), "GET")
        assert get_latest_for_all_projects() == []

    # clear_all() only touches folders named like a sandbox.
    keep = sandboxes.ROOT / "not-a-sandbox"
    keep.mkdir()
    sandboxes.clear_all()
    assert keep.exists() and not any(
        p for p in sandboxes.ROOT.iterdir() if p.name != "not-a-sandbox")
    for bad in ("../x", "abc", "/etc"):
        try:
            sandboxes.use(bad)
        except ValueError:
            continue
        raise AssertionError(f"use({bad!r}) was accepted")
    sandboxes.use(None)
    assert paths.data_dir() == paths.DATA_DIR


def main() -> None:
    check_sessions_and_limits()
    with tempfile.TemporaryDirectory() as tmp:
        seed = Path(tmp) / "seed"
        seed.mkdir()
        (seed / "accounts.json").write_text('[{"id": 1, "text": "Demo"}]')
        with mock.patch.object(sandboxes, "ROOT", Path(tmp) / "boxes"), \
             mock.patch.object(sandboxes, "SEED_DIR", seed):
            check_guard()
            check_sandboxes()
        sandboxes.use(None)
    print("OK - demo sessions / rate limits / guard / sandboxes")


if __name__ == "__main__":
    main()
