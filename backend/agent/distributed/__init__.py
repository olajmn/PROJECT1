"""
"Faculties": capabilities the agent understands independent of which
Room or pipeline stage is asking - reused across more than one of
them, rather than owned by exactly one. Time (backend/agent/distributed/
timeperiod/, backend/agent/distributed/timesegments.py) is the only one with
real code behind it as of 2026-08-24.

Sibling to backend/agent/specialized/ (Rooms - one product concept each).
See docs/08-technical-architecture.md § Faculties for the reasoning,
including why sharing an *implementation pattern* (deterministic
phrase-matching, no LLM guessing) with something in specialized/
(outcome_classifier.py) isn't by itself enough to belong here - a
faculty is measured by reuse across Rooms, not by technique.
"""
