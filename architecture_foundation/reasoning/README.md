# Reasoning

**Status: CURRENT** - established as its own top-level component
(2026-08-27) once Feedback became a second, independent caller
alongside Plan - the condition this file itself set for promotion out
of Planning.

The one boundary every call to a language model passes through: building
the prompt, validating the shape of what comes back, and keeping the model
provider swappable.

## Owns

The raw call to the model - a system+user message in, raw text back.
Used today by `goals/plan/` (JSON plan/step generation) and
`goals/feedback/` (a plain-text acknowledgment); potentially
`../decision/` (phrasing an intervention) or `../knowledge/`
(answering from retrieved context) later. Never decides anything
itself and never validates what the text means - that interpretation
stays with each caller (see `planning/plan/json_request.py`'s
`ask_model()`, `planning/feedback/acknowledger.py`).

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

`backend/model/client.py`'s `send_message()` - the shared
raw call, with two independent callers: `backend/planning/plan/json_request.py`'s
`ask_model()` (JSON-shape validation, Plan-specific) and
`backend/planning/feedback/acknowledger.py`'s `acknowledge()` (plain text,
Feedback-specific, with a deterministic fallback if the call fails).
