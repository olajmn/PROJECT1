"""The one boundary every call to the local model passes through: send
a system+user message, get the raw text response back, retry a bad
shape a few times. Owns nothing about what that text means -
interpreting/validating the response is each caller's own job (see
planning/plan/model_client.py's ask_model(),
planning/feedback/acknowledger.py)."""
