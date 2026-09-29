"""
The activity log shown in Settings → Logs: every saved change across
all projects, newest first.

Nothing is recorded for the log. The events come from
project/timeline.py, which reads the slim tapes in
data/projects/{id}/events.jsonl.
"""

from backend.project.timeline import all_events

# Entries per page; Settings → Logs asks for the next page with "Show
# more" (offset = how many it already has).
LOG_LIMIT = 200


def activity_log(offset: int = 0) -> list[dict]:
    """[{at, project_id, project, event, kind, text}], newest first: one
    page of LOG_LIMIT entries, starting `offset` entries in."""
    return all_events(limit=LOG_LIMIT, offset=offset)
