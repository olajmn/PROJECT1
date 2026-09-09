"""
Deliberately empty as of 2026-08-24 - live external data the agent
could reach out for (weather, calendar, maps, web search, documents),
as opposed to its own hardcoded cognition (backend/foundation/) or its
own recorded history (backend/memory/). Distinct from the USER node
(frontend/, outside backend/ entirely) - World is data pulled in from
outside, User is the human the agent serves.

This project has zero live external-data access today, by design - see
docs/06-development.md's "Aggregation / world-data capability"
entry: a capability the agent could call on, not the core product.
This package exists as a placeholder for where that would eventually
live, not as a signal that it's about to be built - see
docs/03-architecture.md § Faculties for the full reasoning.

Note for whoever adds the first real file here: an empty directory
isn't tracked by git on its own - this __init__.py is also what keeps
this placeholder visible in version control until real code arrives.
"""
