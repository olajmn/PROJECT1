"""
LLM3 - Capability Selection (docs/v4-migration-decision.md).

Decides only WHETHER a capability is needed and WHICH one - never how
that capability should handle the situation (that is the capability's
own job, not LLM3's). Exactly one capability exists today: "project"
(legacy model answers may still say "planning" — accepted and
normalized). Deliberately thin stub — see docs/v4-migration-decision.md.

Receives only Describe's capability-agnostic {"about": ...}, never the
raw user message again.
"""

import json

from backend.llm_client import send_message

SYSTEM_PROMPT = (
    "You decide whether a conversation turn needs a system capability "
    "to run, and if so, which one. The only capability that exists is "
    "\"project\" - for anything about a project the user wants to "
    "orient or co-build a map for, progress on it, or reporting on or "
    "adjusting either. If the message is small talk, a greeting, or "
    "otherwise doesn't call for any capability, respond with null. "
    "Respond with ONLY a JSON object with exactly one key, "
    "\"capability\", whose value is either the string \"project\" or "
    "JSON null."
)


def select_capability(understanding: dict) -> str | None:
    """"project" or None, given Describe's {"about": ...} output only.

    Legacy model answers that still say \"planning\" are accepted and
    normalized to \"project\" for one release (Phase B).
    """
    raw = send_message(SYSTEM_PROMPT, understanding["about"], json_mode=True)
    data = json.loads(raw)
    capability = data.get("capability")
    if capability == "project":
        return "project"
    if capability == "planning":
        return "project"
    return None
