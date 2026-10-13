"""
Public demo mode (docs/05-decisions.md #70, docs/public-demo-plan.md): one
shared password, sessions, and limits in front of the API. Off unless
DEMO_MODE is set; then requests_from_browser.Handler passes every
request through guard() first.
"""

from backend.api.demo.check import guard
from backend.api.demo.settings import ENABLED

__all__ = ["ENABLED", "guard"]
