"""
Agent — conversation roles, capability routing, surface text, and the
free-conversation turn.

Voice and Describe talk and interpret; Node 3 (llm3) selects whether
Project applies; manifestation turns Project state into text/tree the
UI and Voice may see; process_turn.py runs one free-conversation turn
(Describe → select → Project or Voice). Project-scoped chat stays in
backend.project.panes.chat.
"""
