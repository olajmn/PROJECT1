"""
The named dimensions a Goal's planability is assessed along - the
question list, not a set of required answers.

docs/planning-model.md § Minimum planability rejects "a checklist of
fields ... that must all be filled in before anything can happen", and
nothing here reinstates one: no slot is mandatory, and a Goal can be
planned with several still UNRESOLVED. What is fixed is only WHICH
dimensions get considered, so that the same Goal is weighed the same
way twice. The verdict per dimension stays a live judgment, made
against § The gate's three states.

Naming the dimensions while leaving the verdicts free is the same
trick that stabilized backend/planning/plan/zoom.py: fix the shape of
the question, let the model fill the content. Instability there came
from the model re-deciding what to even produce on each call; the
analogous instability here is it re-deciding what is worth asking
about at all, so one Goal gets a timeframe question and an identical
one gets none.

Deliberately four, and deliberately not the six § Minimum planability
enumerates. A named dimension is a standing invitation to find
something missing in it, and the local model takes that invitation
every time - six would reliably produce six questions before any plan
appeared, which is a worse failure than the vagueness it was meant to
fix. DESIRED_STATE is left out as largely covered by CONTENT, and
CONSTRAINTS as an open-ended catch-all with no natural stopping point.

Data only, no logic and no model call - the same split as
foundation/time/time_data/time_units.py. Nothing reads this yet;
_planability() still returns one verdict for a whole Goal rather than
one per slot.
"""

# Whether the agent may contribute content toward an unresolved slot,
# or only name it and stop - docs/planning-model.md § ASK vs. SUGGEST.
# SUGGEST is allowed exactly where generic, non-personal reasoning gets
# meaningfully closer to an answer. It is therefore NOT a property of
# how important a slot is, but of whether an answer could come from
# anywhere other than this specific user: § The gate's KNOWN "never
# covers anything personal to this specific user that hasn't been
# stated", which rules out proposing a default for one.
ASK_ONLY = "ask_only"
SUGGESTIBLE = "suggestible"


class Slot:
    """One dimension, with the two facts that decide how an unresolved
    verdict on it is allowed to be acted on."""

    def __init__(self, name: str, question: str, unresolved_move: str, filled_by_code: bool = False):
        self.name = name
        # What the dimension actually asks - phrased as the thing to be
        # established, not as wording to show the user. Producing the
        # sentence a person sees is Voice's job (backend/llm_roles/voice.py).
        self.question = question
        self.unresolved_move = unresolved_move
        # True where deterministic code already resolves this without
        # the model being asked - "code decides, model is just told"
        # (docs/05-decisions.md, 2026-08-23).
        self.filled_by_code = filled_by_code


CONTENT = Slot(
    name="content",
    question="what specifically the user wants to achieve, concretely enough that two different plans for it would not be equally valid",
    # A safe, generic first step can exist without knowing anything
    # personal - this is the slot generate_plan()'s `suggested_action`
    # already serves.
    unresolved_move=SUGGESTIBLE,
)

TIME = Slot(
    name="time",
    question="the span the plan has to fit inside",
    # The one SUGGEST behavior actually built and measured
    # (`suggested_duration`) - see § Time-sufficiency.
    unresolved_move=SUGGESTIBLE,
    # extract_duration_phrase() searches the typed text before any
    # model call, and its result wins over the model second-guessing
    # it (see generate_plan()).
    filled_by_code=True,
)

CURRENT_STATE = Slot(
    name="current_state",
    question="where the user is now relative to the goal",
    # Personal and unstated by definition - a proposed default here
    # would be an assumption about this user dressed as generic
    # reasoning, which § ASK vs. SUGGEST's genericness test rejects.
    unresolved_move=ASK_ONLY,
)

CAPACITY = Slot(
    name="capacity",
    question="how much time or effort the user can actually give this, per week or per day",
    # Same reason as CURRENT_STATE. Note this is what a practice's
    # rate would be measured against (docs/concepts.md § 4.ix), so it
    # is the one slot whose absence blocks a recurring commitment
    # entirely rather than only coarsening a plan.
    unresolved_move=ASK_ONLY,
)

# Order is the order to weigh them in, not a sequence of questions to
# march through: CONTENT first because every other slot's answer is
# read relative to what the goal turns out to be, TIME second for the
# same reason generate_structure() returns None without a resolvable
# span. The two ASK_ONLY slots come last because they are the ones a
# plan can most often be produced without - see § The necessity test,
# which asks what a specific unknown actually blocks rather than
# closing every unknown up front.
SLOTS = (CONTENT, TIME, CURRENT_STATE, CAPACITY)
