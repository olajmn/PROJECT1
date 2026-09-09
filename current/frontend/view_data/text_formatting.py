"""
Text Formatting

Pure text presentation for frontend templates - joining and splitting
text for display. No Flask or backend/domain dependency.
"""


def join_plan_prose(texts: list[str]) -> str:
    """
    Join filled-horizon text into one paragraph. The model doesn't
    reliably end a horizon's text with punctuation, so a bare
    space-join reads as one run-on sentence - each piece's trailing
    punctuation is stripped and re-joined with ". " instead. Empty
    input returns "". This format is what split_message_lines() expects below.
    """
    cleaned = [text.strip().rstrip(".") for text in texts if text]
    if not cleaned:
        return ""
    return ". ".join(cleaned) + "."


def split_message_lines(text: str) -> list[str]:
    """
    Split a joined message back into sentence-like parts for display -
    the stored text itself is untouched, still one plain string
    everywhere else. A plain ". ".split() would silently swallow the
    period from every part but the last, since join_plan_prose() uses
    it as the separator; re-added here to any part that doesn't
    already end in its own sentence-ending punctuation.
    """
    if not text:
        return []
    parts = [p for p in text.split(". ") if p]
    return [
        p if i == len(parts) - 1 or p.rstrip().endswith((".", "!", "?", ":")) else p.rstrip() + "."
        for i, p in enumerate(parts)
    ]
