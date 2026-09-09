"""
Small, direct checks for math.py's four operations - not a test
framework, just asserts run top to bottom. Covers positive/negative/
decimal/zero operands and division by zero, not exhaustive coverage.

Run from the project root:
    .venv/bin/python -m backend.foundation.test_math
"""

# Contents
#  1. Basic arithmetic cases
#      - ADD_CASES
#      - SUBTRACT_CASES
#      - MULTIPLY_CASES
#      - DIVIDE_CASES
#
#  2. Division by zero

from backend.foundation.math import add, divide, multiply, subtract

# 1. Basic arithmetic cases

# (a, b, expected)
ADD_CASES = (
    (2, 3, 5),
    (-2, -3, -5),
    (-5, 3, -2),
    (2.5, 0.5, 3.0),
    (0, 5, 5),
    (0, 0, 0),
)

SUBTRACT_CASES = (
    (5, 3, 2),
    (-5, -3, -2),
    (3, 5, -2),
    (2.5, 0.5, 2.0),
    (5, 0, 5),
    (0, 0, 0),
)

MULTIPLY_CASES = (
    (2, 3, 6),
    (-2, -3, 6),
    (-2, 3, -6),
    (2.5, 2, 5.0),
    (5, 0, 0),
    (0, 0, 0),
)

DIVIDE_CASES = (
    (6, 3, 2),
    (-6, -3, 2),
    (-6, 3, -2),
    (5, 2, 2.5),
    (0, 5, 0),
)

for a, b, expected in ADD_CASES:
    result = add(a, b)
    assert result == expected, f"add({a}, {b}) = {result}, expected {expected}"

for a, b, expected in SUBTRACT_CASES:
    result = subtract(a, b)
    assert result == expected, f"subtract({a}, {b}) = {result}, expected {expected}"

for a, b, expected in MULTIPLY_CASES:
    result = multiply(a, b)
    assert result == expected, f"multiply({a}, {b}) = {result}, expected {expected}"

for a, b, expected in DIVIDE_CASES:
    result = divide(a, b)
    assert result == expected, f"divide({a}, {b}) = {result}, expected {expected}"

# 2. Division by zero

# Positive, negative, and zero dividend - must always raise, never
# return 0/None/infinity.
for a in (5, -5, 0):
    try:
        divide(a, 0)
        raise AssertionError(f"divide({a}, 0) did not raise ZeroDivisionError")
    except ZeroDivisionError:
        pass

total_cases = len(ADD_CASES) + len(SUBTRACT_CASES) + len(MULTIPLY_CASES) + len(DIVIDE_CASES) + 3
print(f"OK - {total_cases} case(s) passed (including 3 division-by-zero case(s))")
