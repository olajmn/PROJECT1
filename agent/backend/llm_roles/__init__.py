"""
Shared conversation roles - Voice and Describe.

Same path level under `backend/` as `planning/` and
`global_conversation/`, but not a domain and not an entry
orchestrator: reusable LLM *roles* any caller may invoke.

- Voice (`voice.py`) - talk to the user (was `llm1/`)
- Describe (`describe.py`) - one neutral sentence about the message
  (was `llm2/` / Understand)

Decide / Stage 3 is documented in `decide.md`. Stage 3 Decide lives in
`planning/plan/decide.py`; Fill orchestration in `generate_plan.py`
(not this package). The old `backend/llm3/` gate is only global
small-talk vs Planning - not Stage 3.
"""

from backend.llm_roles.describe import describe, describe_in_context
from backend.llm_roles.voice import respond

__all__ = ["respond", "describe", "describe_in_context"]
