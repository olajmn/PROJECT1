"""
LLM3 - Capability Selection (docs/v4-migration-decision.md).

Decides only WHETHER a capability is needed and WHICH one - never how
that capability should handle the situation (that is the capability's
own job, not LLM3's). Exactly one capability exists today: "planning".
This is a deliberately thin stub, not real multi-capability reasoning
- see docs/v4-migration-decision.md, "Planning is the first capability."

Receives only LLM2's capability-agnostic understanding, never the raw
user message again - LLM3 works from what LLM2 already produced,
consistent with the data-flow direction in docs/v4-migration-decision.md.
"""

import json

from backend.reasoning.model_client import send_message

SYSTEM_PROMPT = (
    "You decide whether a conversation turn needs a system capability "
    "to run, and if so, which one. The only capability that exists is "
    "\"planning\" - for anything about a goal the user wants to "
    "achieve, a plan, progress, or reporting on or adjusting either. "
    "If the message is small talk, a greeting, or otherwise doesn't "
    "call for any capability, respond with null. Respond with ONLY a "
    "JSON object with exactly one key, \"capability\", whose value is "
    "either the string \"planning\" or JSON null."
)


def select_capability(understanding: dict) -> str | None:
    """"planning" or None, given LLM2's {"about": ...} output only."""
    raw = send_message(SYSTEM_PROMPT, understanding["about"], json_mode=True)
    data = json.loads(raw)
    capability = data.get("capability")
    return capability if capability == "planning" else None
