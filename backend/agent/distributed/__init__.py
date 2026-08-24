"""
Broad faculties: capabilities the agent understands independent of
which narrow faculty or pipeline stage is asking - reused across more
than one of them, rather than owned by exactly one. Time
(backend/agent/distributed/timeperiod/,
backend/agent/distributed/timesegments.py) is the only one with real
code behind it as of 2026-08-24.

Sibling to backend/agent/specialized/ (narrow faculties - one product
concept each). See docs/08-technical-architecture.md § Faculties for
the reasoning, including why sharing a Cognition/Recognition pair
(fixed rules + matching logic that applies them, deterministic, no LLM
guessing) with something in specialized/ (outcome_classifier.py +
outcome_phrases.py) isn't by itself enough to belong here - breadth is
measured by reuse, not by which pattern it's built from.
"""
