"""
Narrow faculties: one clearly-scoped product concept per file, each
doing one job that belongs to it alone - Goal, Plan, Task, and the
deterministic feedback classifier tied specifically to Goal's own
feedback flow. ("Faculty" is this project's word for what's plainly
called a module elsewhere - see docs/08-technical-architecture.md §
Faculties, terminology note.)

Sibling to backend/agent/distributed/ (broad faculties - reused by
more than one narrow faculty; Time today). Contrast is the whole
point: see docs/08-technical-architecture.md § Faculties for what
decides whether something belongs here or there, and why storage.py
belongs to neither and stays at backend/'s own root instead.
"""
