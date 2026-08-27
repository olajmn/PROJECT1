"""Parses free-text feedback into action_completed/action_not_completed/
action_in_progress/goal_completed, or a duration-change request
(feedback_parser.py). Also owns generating a display-only
acknowledgment for feedback that couldn't be classified
(acknowledger.py) - never a decision, never able to influence one."""
