# Conversation

**Status: NEXT** - a real, identified gap. Named in the prototype's own
architecture docs, never built as its own thing.

The raw exchange of messages between user and agent, independent of what
domain a given message eventually resolves into (Goal feedback, a new
Goal, a Knowledge question, small talk, an answer to a pending
clarification).

## Owns

The message thread itself, before interpretation decides what it's about.

## Boundary

Not the same as a Goal's own history thread. In the prototype today, a
goal's "conversation" (see `goals/feedback/`) only ever exists as a side
effect of that one goal's feedback records - there's no message log
independent of a specific goal. A real Conversation component would sit
upstream of `goals/`, `knowledge/`, and anything else a message might be
routed to, not owned by any single one of them.

## Reference implementation

None yet. `devtools/html/active_goal/_conversation.html` in the prototype
renders something conversation-shaped, but it's a per-goal view built from
`goals/feedback/` records, not an independent Conversation capability.
