"""
The activity log shown in Settings → Logs: every saved change across
all projects, newest first.

Nothing is recorded for the log. The events come from
project/timeline.py, which reads the timestamped lines in
data/plans.jsonl.
"""

from backend.project.timeline import all_events

# Newest entries shown; the rest stay in plans.jsonl.
LOG_LIMIT = 200


def activity_log() -> list[dict]:
    """[{at, project_id, project, event, kind, text}], newest first."""
    return all_events(limit=LOG_LIMIT)
