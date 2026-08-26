# Reasoning

**Status: NEXT** - works today, but only informally, buried inside Planning.
Worth making an explicit boundary before more components need to call a
model.

The one boundary every call to a language model passes through: building
the prompt, validating the shape of what comes back, and keeping the model
provider swappable.

## Owns

Prompt construction and response validation for any component that needs a
model - `goals/plan/` today; potentially `../decision/` (phrasing an
intervention) or `../knowledge/` (answering from retrieved context) later.
Never decides anything itself - it's a mechanism boundary, not a
decision-maker.

## Boundary

- The LLM itself is a mechanism inside this component, not a component of
  its own - see `ARCHITECTURE.md`.
- Deterministic judgment calls (does this text report completion? is this
  a real duration phrase?) do not belong here - see `goals/feedback/` and
  the prototype's own "code decides, the model is told" principle. This
  component reasons in language; it doesn't replace decisions code can
  make outright.
- `../user_model/` deliberately does not go through this component - it's
  meant to stay non-LLM, statistical, and directly inspectable (see that
  component's README).

## Also upstream: Interpretation/Parsing

Not a separate top-level component in this skeleton, but worth naming: the
general pattern `goals/feedback/` is one instance of - deterministic
interpretation of free text into a structured signal, admitting "don't
know" rather than guessing - recurs anywhere raw user input needs to become
something the rest of the system can act on (a new Goal's text, a
clarification answer, a duration phrase). See `ARCHITECTURE.md`'s flow
diagram, where it sits between Conversation and Memory.

## Reference implementation

`backend/planning/plan.py`'s `_ask_model()` - shared shape-validation
already exists, just scoped to Planning alone rather than factored out as
its own boundary.
