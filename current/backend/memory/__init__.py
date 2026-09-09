"""
Deliberately empty - the agent's own raw operational history (every
Goal, Plan, Action, Feedback) as a first-class, read-only capability,
distinct from Knowledge (user-supplied material, see backend/world/'s
neighboring reasoning) and from being an implicit side effect of
reading goals/goal/resolver.py directly.

The raw data this would read already exists and is complete -
infrastructure/data_persistence.py's load_history(), and
goals/goal/resolver.py's get_history_for_goal() - what's missing is
organizing access to it as its own capability. Not built yet; a
top-level Domain (sibling to goals/, foundation/, world/), not a
Faculty nested under foundation/ - see
architecture_foundation/memory/README.md.

Note for whoever adds the first real file here: an empty directory
isn't tracked by git on its own - this __init__.py is also what keeps
this placeholder visible in version control until real code arrives.
"""
