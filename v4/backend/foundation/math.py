"""
Math
====

Deterministic, LLM-free arithmetic - so a real numeric computation is
always done in code, never guessed by the model (same "code decides,
the model is told" reasoning as foundation/time/, see
docs/03-architecture.md). A Faculty - quantitative reasoning, the same
principled status as foundation/time/'s temporal understanding (see
docs/03-architecture.md § Math and docs/05-decisions.md, "Faculty
categorization") - other parts of the system can use these instead of
writing their own small numeric operations.

First version: the four basic operations only. No percentages,
algebra, statistics, trigonometry, or expression parsing yet - add
those only once something actually needs them.

A single flat module, not a package - four functions don't need
time/'s data/logic split (there's no separate table of facts here to
split out); grow this into a package only if/when real complexity
shows up.
"""

# Contents
#  1. Basic arithmetic
#      - add()
#      - subtract()
#      - multiply()
#      - divide()


# 1. Basic arithmetic


def add(a: int | float, b: int | float) -> int | float:
    """a + b."""
    return a + b


def subtract(a: int | float, b: int | float) -> int | float:
    """a - b."""
    return a - b


def multiply(a: int | float, b: int | float) -> int | float:
    """a * b."""
    return a * b


def divide(a: int | float, b: int | float) -> float:
    """
    a / b.

    Raises ZeroDivisionError if `b` is 0 - explicit, not just Python's
    own implicit division-by-zero behavior - so an undefined result
    never gets silently coerced into 0/None/infinity by a caller
    upstream; it fails loudly instead.
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero.")
    return a / b
