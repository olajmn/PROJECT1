"""
Demo-mode settings, read once from the environment when the server
starts (docs/demo.md). None of them matter unless
DEMO_MODE is set.
"""

import os


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _number(name: str, default: int) -> int:
    return int(os.environ.get(name, "").strip() or default)


ENABLED = _flag("DEMO_MODE")
PASSWORD = os.environ.get("DEMO_PASSWORD", "")
if ENABLED and not PASSWORD:
    # Fails at start: demo mode without a password would leave the API open.
    raise ValueError("DEMO_MODE is set but DEMO_PASSWORD is empty")

# A session ends after this long without a request, or this long after
# login, whichever comes first. Read from the environment so a smoke
# test can shorten them.
IDLE_SECONDS = _number("DEMO_IDLE_SECONDS", 30 * 60)
MAX_SECONDS = _number("DEMO_MAX_SECONDS", 8 * 60 * 60)
MAX_SESSIONS = _number("DEMO_MAX_SESSIONS", 50)

# How many levels below the top a project's map opens with in the demo,
# for a visitor who has not chosen a depth with − / + yet. Outside the
# demo the map picks a depth that fits the whole tree on screen.
MAP_START_DEPTH = _number("DEMO_MAP_START_DEPTH", 3)

# The project a first-time visitor sees opened (a project_id from the
# seed); 0 leaves the choice to the app.
START_PROJECT_ID = _number("DEMO_START_PROJECT_ID", 0)

# Secure cookies are only sent over HTTPS. DEMO_INSECURE_COOKIE=1 is for
# trying demo mode on http://localhost, never for the public host.
SECURE_COOKIE = not _flag("DEMO_INSECURE_COOKIE")

# Only set behind a proxy that writes this header itself (e.g.
# Fly-Client-IP); without one, a client could send any IP it likes.
CLIENT_IP_HEADER = os.environ.get("DEMO_CLIENT_IP_HEADER", "").strip()

# A pasted outline is the largest body the app sends.
BODY_MAX_BYTES = 256 * 1024
# A chat body is the message plus a few focus fields.
CHAT_BODY_MAX_BYTES = 8 * 1024
LOGIN_BODY_MAX_BYTES = 1024

# (count, seconds): at most `count` in any `seconds`.
# Only wrong passwords count, so logging in and out again is never blocked.
LOGIN_FAILURES_PER_IP = (10, 15 * 60)
TALK_PER_SESSION = (10, 60)
TALK_PER_IP = (20, 60)
TALK_PER_DAY = (_number("DEMO_TALK_PER_DAY", 500), 24 * 60 * 60)
