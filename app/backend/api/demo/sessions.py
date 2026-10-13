"""
Demo sessions, in memory only: a restart logs everyone out. A session
is a random token with the time it was created and last used; it ends
on logout, after `idle` seconds without a request, or `max_age` seconds
after login.
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


class Sessions:
    def __init__(
        self,
        idle: float,
        max_age: float,
        limit: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
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
            self._sweep(now)
            if len(self._by_token) >= self._limit:
                return None
            session = Session(secrets.token_urlsafe(32), now, now)
            self._by_token[session.token] = session
            return session

    def get(self, token: str | None) -> Session | None:
        """The open session for `token`, marked as used now; None if there
        is none or it has expired (an expired one is removed)."""
        if not token:
            return None
        with self._lock:
            now = self._clock()
            session = self._by_token.get(token)
            if session is None:
                return None
            if self._expired(session, now):
                del self._by_token[token]
                return None
            session.last_seen = now
            return session

    def end(self, token: str | None) -> None:
        with self._lock:
            self._by_token.pop(token or "", None)

    def count(self) -> int:
        with self._lock:
            self._sweep(self._clock())
            return len(self._by_token)

    def _expired(self, session: Session, now: float) -> bool:
        return (
            now - session.last_seen > self._idle
            or now - session.created > self._max_age
        )

    def _sweep(self, now: float) -> None:
        for token in [t for t, s in self._by_token.items() if self._expired(s, now)]:
            del self._by_token[token]
