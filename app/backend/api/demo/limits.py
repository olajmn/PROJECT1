"""
Rate limits for demo mode, in memory: at most `count` events per
`window` seconds for each key (an IP, a session token, or one shared
key for a whole-demo cap). A restart clears them.
"""

import threading
import time
from collections import deque
from typing import Callable


class RateLimit:
    def __init__(
        self,
        count: int,
        window: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._count = count
        self._window = window
        self._clock = clock
        self._lock = threading.Lock()
        self._events: dict[str, deque[float]] = {}

    def full(self, key: str) -> bool:
        """True when `key` is at the limit; records nothing."""
        with self._lock:
            return len(self._recent(key, self._clock())) >= self._count

    def allow(self, key: str) -> bool:
        """Record one event for `key` and return True, or return False
        (and record nothing) when `key` is already at the limit."""
        with self._lock:
            now = self._clock()
            events = self._recent(key, now)
            if len(events) >= self._count:
                return False
            events.append(now)
            return True

    def _recent(self, key: str, now: float) -> deque[float]:
        """`key`'s events inside the window (lock held)."""
        events = self._events.setdefault(key, deque())
        while events and now - events[0] >= self._window:
            events.popleft()
        return events
