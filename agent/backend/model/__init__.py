"""The one boundary every call to the local model passes through: send
a system+user message, get the raw text response back, retry a bad
shape a few times. Owns nothing about what that text means -
interpreting/validating the response is each caller's own job (see
planning/plan/json_request.py's ask_model(),
planning/feedback/acknowledger.py).

Named for what it holds - the model boundary - not for reasoning,
which happens in the callers, not here."""
