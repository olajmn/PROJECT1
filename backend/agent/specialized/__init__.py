"""
"Rooms": one clearly-scoped product concept per file, each doing one
job that belongs to it alone - Goal, Plan, Task, and the deterministic
feedback classifier tied specifically to Goal's own feedback flow.

Sibling to backend/agent/distributed/ (capabilities more than one Room
leans on - Time today). Contrast is the whole point: see
docs/08-technical-architecture.md § Faculties for what decides whether
something belongs here or there, and why storage.py belongs to neither
and stays at backend/'s own root instead.
"""
