"""The talk chart: which conversation grew out of which.

- Messages in a row about the same selected node = one entry.
- Switching straight to another node puts the new entry under the
  one you left (it grew out of it).
- Chatting with no node selected ends the branch; those messages are
  not shown in the chart.

Built from the chat thread each time. Nothing saved. Not the node map.
"""

from __future__ import annotations


def talk_tree(messages: list[dict]) -> list[dict]:
    """[{label, start, end, open, children, focus_step_id?}] for
    focused stretches, oldest first. `start`/`end` are indices into
    `messages` (`end` exclusive)."""
    roots: list[dict] = []
    stack: list[dict] = []
    index = 0
    count = len(messages)

    while index < count:
        label = _focus(messages[index])
        end = index + 1
        while end < count and _focus(messages[end]) == label:
            end += 1
        if label:
            node = {
                "label": label,
                "start": index,
                "end": end,
                "open": end == count,
                "children": [],
            }
            step = _step_id(messages, index, end)
            if step:
                node["focus_step_id"] = step
            if stack:
                stack[-1]["open"] = False
                stack[-1]["children"].append(node)
            else:
                roots.append(node)
            stack.append(node)
        else:
            stack.clear()
        index = end

    return roots


def _focus(message: dict) -> str | None:
    return (message.get("focus") or "").strip() or None


def _step_id(messages: list[dict], start: int, end: int) -> str | None:
    for message in messages[start:end]:
        step = (message.get("focus_step_id") or "").strip()
        if step:
            return step
    return None
