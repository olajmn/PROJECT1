"""
Module vocabulary and constants - module_library's five reasoning
functions. Each one is a real, usable constant below, re-exporting its
callable under a shared name - a Node imports it from here rather than
reaching into each module's own file directly.

Every module has the exact same shape: (text, purpose, context=None).
None of the five knows the other four exist, and none inspects where
`context` came from - composing them (deciding what to pass forward as
one module's `context` for the next) is the calling Node's own job,
never something baked into a module itself. This is what keeps each
module genuinely reusable on its own, not only reusable together.
"""

from backend.module_library.critique import critique
from backend.module_library.hypothesis import hypothesize
from backend.module_library.interpretation import interpret
from backend.module_library.reasoning import reason
from backend.module_library.synthesis import synthesize

# ============================================================
# Interpretation (I)
# ============================================================

# Distinguishes what is explicitly stated, what would only be an
# inference, and which specific terms are themselves ambiguous, given
# the purpose the text is read for. Does not decide what happens
# next. See interpretation.py:
#     interpret(text, purpose, context=None)
#     -> {"explicit": str, "inferred": [str, ...],
#         "ambiguous_terms": [{"term": str, "meanings": [str, ...]}, ...]}
INTERPRETATION = interpret

# ============================================================
# Hypothesis (H)
# ============================================================

# Generates several distinct, plausible explanations or possibilities
# for a piece of text - without picking, ranking, or evaluating any
# of them. See hypothesis.py:
#     hypothesize(text, purpose, context=None)
#     -> {"hypotheses": [str, ...]}
HYPOTHESIS = hypothesize

# ============================================================
# Critique (C)
# ============================================================

# Identifies weaknesses, unsupported assumptions, or contradictions
# in a piece of text (or in specific claims passed via `context`) -
# never proposes a fix or introduces a new hypothesis. See
# critique.py:
#     critique(text, purpose, context=None)
#     -> {"critiques": [{"target": str, "weakness": str}, ...]}
CRITIQUE = critique

# ============================================================
# Reasoning (R)
# ============================================================

# Works out what actually follows from a piece of text and what
# remains genuinely unresolved - an analytical conclusion, never an
# executable plan (that stays the Planning capability's own job, see
# planning/). See reasoning.py:
#     reason(text, purpose, context=None)
#     -> {"conclusion": str, "open_questions": [str, ...]}
REASONING = reason

# ============================================================
# Synthesis (S)
# ============================================================

# Produces the one result a Node actually acts on or shows, given a
# piece of text and whatever context the caller supplies - the only
# module whose output is meant to be consumed outside module_library.
# See synthesis.py:
#     synthesize(text, purpose, context=None)
#     -> {"result": str}
SYNTHESIS = synthesize
