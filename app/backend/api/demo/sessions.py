"""
Demo sessions, in memory only: a restart logs everyone out. A session
is a random token with the time it was created and last used, and the
id of the visitor's sandbox; it ends on logout, after `idle` seconds
without a request, or `max_age` seconds after login. `on_end` runs for
every session that ends, whichever way.
"""

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Session:
    token: str
    created: float
    last_seen: float
    sandbox: str | None = None


class Sessions:
    def __init__(
        self,
        idle: float,
        max_age: float,
        limit: int,
        clock: Callable[[], float] = time.monotonic,
        on_end: Callable[[Session], None] | None = None,
    ) -> None:
        self._on_end = on_end
        self._idle = idle
        self._max_age = max_age
        self._limit = limit
        self._clock = clock
        self._lock = threading.Lock()
        self._by_token: dict[str, Session] = {}

    def create(self) -> Session | None:
        """A new session, or None when `limit` sessions are already open."""
        with self._lock:
            now = self._clock()
            ended = self._sweep(now)
            full = len(self._by_token) >= self._limit
            if not full:
                session = Session(secrets.token_urlsafe(32), now, now)
                self._by_token[session.token] = session
        self._ended(ended)
        return None if full else session

    def get(self, token: str | None) -> Session | None:
        """The open session for `token`, marked as used now; None if there
        is none or it has expired (an expired one is removed)."""
        if not token:
            return None
        with self._lock:
            ended = self._sweep(self._clock())
            session = self._by_token.get(token)
            if session is not None:
                session.last_seen = self._clock()
        self._ended(ended)
        return session

    def end(self, token: str | None) -> None:
        with self._lock:
            session = self._by_token.pop(token or "", None)
        self._ended([session] if session else [])

    def count(self) -> int:
        with self._lock:
            ended = self._sweep(self._clock())
            count = len(self._by_token)
        self._ended(ended)
        return count

    def _expired(self, session: Session, now: float) -> bool:
        return (
            now - session.last_seen > self._idle
            or now - session.created > self._max_age
        )

    def _sweep(self, now: float) -> list[Session]:
        """Remove expired sessions (lock held) and return them."""
        ended = [s for s in self._by_token.values() if self._expired(s, now)]
        for session in ended:
            del self._by_token[session.token]
        return ended

    def _ended(self, sessions: list[Session]) -> None:
        # Outside the lock: on_end removes a folder, which can take a moment.
        if self._on_end:
            for session in sessions:
                self._on_end(session)
