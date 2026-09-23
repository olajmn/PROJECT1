"""
Shared conversation roles - Voice and Describe.

Lives under `backend.agent` with manifestation. Not a domain and not
an entry orchestrator: reusable LLM *roles* any caller may invoke.

- Voice (`voice.py`) - talk to the user (was `llm1/`)
- Describe (`describe.py`) - one neutral sentence about the message
  (was `llm2/` / Understand)

Stage 3 is gone. See `roles.md` for the Voice / Describe map.
"""

from backend.agent.llm_roles.describe import describe, describe_in_context
from backend.agent.llm_roles.voice import respond

__all__ = ["respond", "describe", "describe_in_context"]
