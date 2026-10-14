"""
Public demo mode (docs/05-decisions.md #70, docs/demo.md): one
shared password, sessions, and limits in front of the API. Off unless
DEMO_MODE is set; then requests_from_browser.Handler passes every
request through guard() first.
"""

from backend.api.demo.check import guard
from backend.api.demo.settings import ENABLED, MAP_START_DEPTH, START_PROJECT_ID

__all__ = ["ENABLED", "MAP_START_DEPTH", "START_PROJECT_ID", "guard"]
