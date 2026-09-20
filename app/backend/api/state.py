"""
Process-wide API state — Session mint on boot.

Owned by backend.api (not agent/ or project/): HTTP adapters need a
place for request-spanning pointers that are not domain logic.
"""

# Contents
#  1. Session mint (process bookkeeping)
#      - start_session() once at import

from backend.store.session import start_session


# ============================================================
# 1. Session mint (process bookkeeping)
# ============================================================

# One Session record per HTTP process start — same timing as the old
# free-conversation Session() side effect, without ChatFocus. No UI
# surfaces this yet (Log → Sessions was removed 2026-09-20).
start_session()
