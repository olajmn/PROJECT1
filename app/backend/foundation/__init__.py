"""
Faculties: what the agent understands, organized by topic. Two
Faculties are established: time/ (temporal understanding) and math.py
(quantitative reasoning) - a Faculty has to be earned, either through
demonstrated reuse or by representing a genuine, independently-existing
reasoning domain, not proposed as a plausible category (see
docs/05-decisions.md, "Faculty categorization"). Replaces the earlier
agent/specialized/ vs agent/distributed/ reuse-based split. agent/ is
gone entirely as of 2026-08-25: Goal (and, as of 2026-08-27, Plan)
moved to backend/goals/, a Domain and sibling of this package rather
than nested inside it. Also sibling to backend/world/ (external data)
and backend/memory/ (agent's own history - a Domain, not a Faculty
under this package, despite the similar-sounding name).
"""
