"""
Text Formatting

Pure text presentation for frontend's templates - converting between a
list of text pieces and one displayable string, in both directions. No
Flask dependency, no backend/domain dependency - doesn't know what a
Goal, Vision, or Plan is, only that it's been handed some text to
join or split for display.
"""


def join_plan_prose(texts: list[str]) -> str:
    """
    Join a plan's filled-horizon sentences into one flowing paragraph
    (see frontend/templates/active_goal/_plan.html). Strips each piece's own
    trailing punctuation/whitespace before re-joining with ". " and a
    final period, rather than a bare space - the model doesn't
    consistently end a horizon's text with a period itself, so a plain
    space-join produces run-on-looking text with no visible sentence
    boundary (e.g. "...long-term Develop a meal planning system...").
    Empty string for an empty list - nothing to join, same as the
    template's own empty check.

    A DISPLAY concern (how frontend renders a plan), not Plan-domain
    logic - see split_message_lines() below, its exact reverse.
    """
    cleaned = [text.strip().rstrip(".") for text in texts if text]
    if not cleaned:
        return ""
    return ". ".join(cleaned) + "."


def split_message_lines(text: str) -> list[str]:
    """
    Split one chat message into its separate sentence-like parts, for
    active_goal/_conversation.html's thread to render each on
    its own line - a message built from more than one thought (e.g.
    app.py's own "Checked in (couldn't tell what this means yet). Note:
    {note}") otherwise reads as one dense run-on block instead of the
    distinct statements it actually is. Purely a DISPLAY concern (how
    frontend renders a string), not a data concern - the stored
    `feedback`/`right_now`/etc. text itself is untouched, still one
    plain string everywhere else (goal_log/history.html, _plan_entry.html, the
    JSON file itself).

    The exact reverse of join_plan_prose() above (". ".join
    of several texts): splits back on that same separator. A plain
    ". ".split() would silently swallow the period from every part
    except the last (join_plan_prose's job was gluing them INTO one
    string, so the separator eats it) - re-added here to each part that
    doesn't already end in its own sentence-ending punctuation, so a
    part like "Checked in (couldn't tell what this means yet)" reads as
    a complete sentence again once it's back on its own line.
    """
    if not text:
        return []
    parts = [p for p in text.split(". ") if p]
    return [
        p if i == len(parts) - 1 or p.rstrip().endswith((".", "!", "?", ":")) else p.rstrip() + "."
        for i, p in enumerate(parts)
    ]
