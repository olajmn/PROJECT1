"""Checks for openrouter.chat() and the provider switch in client.py - no
network, no real key, no model call. Run from app/:

    .venv/bin/python -m backend.model.test_openrouter
"""

import importlib
import io
import json
import os
import urllib.error
from unittest import mock

from backend.model import client, openrouter

FAKE_KEY = "test-key-not-real"
MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "hi"},
]


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _reply(payload: dict) -> _Response:
    return _Response(json.dumps(payload).encode())


def _raises(call, error=openrouter.OpenRouterError) -> str:
    try:
        call()
    except error as e:
        return str(e)
    raise AssertionError(f"expected {error.__name__}")


def check_openrouter() -> None:
    with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
        assert _raises(lambda: openrouter.chat("m", MESSAGES, 0.2)) == "OPENROUTER_API_KEY is not set"

    with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": FAKE_KEY}):
        ok = _reply({"choices": [{"message": {"content": "Hello."}}]})
        with mock.patch("urllib.request.urlopen", return_value=ok) as urlopen:
            assert openrouter.chat("qwen/qwen3.5-9b", MESSAGES, 0.2) == "Hello."
        request = urlopen.call_args.args[0]
        sent = json.loads(request.data)
        assert sent["model"] == "qwen/qwen3.5-9b"
        assert sent["messages"] == MESSAGES
        assert sent["temperature"] == 0.2
        assert sent["reasoning"] == {"enabled": False}
        assert sent["max_tokens"] == openrouter.MAX_TOKENS
        assert request.get_header("Authorization") == f"Bearer {FAKE_KEY}"
        assert urlopen.call_args.kwargs["timeout"] == openrouter.TIMEOUT_SECONDS

        # Errors say what failed, never the key or the response body.
        unauthorized = urllib.error.HTTPError(
            openrouter.URL, 401, "Unauthorized", {}, io.BytesIO(FAKE_KEY.encode()))
        with mock.patch("urllib.request.urlopen", side_effect=unauthorized):
            message = _raises(lambda: openrouter.chat("m", MESSAGES, 0.2))
        assert message == "HTTP 401" and FAKE_KEY not in message

        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError()):
            assert _raises(lambda: openrouter.chat("m", MESSAGES, 0.2)) == "request failed: TimeoutError"

        upstream = _reply({"error": {"message": "provider down", "code": 502}})
        with mock.patch("urllib.request.urlopen", return_value=upstream):
            assert _raises(lambda: openrouter.chat("m", MESSAGES, 0.2)) == "no reply in response"

        empty = _reply({"choices": [{"message": {"content": "  "}}]})
        with mock.patch("urllib.request.urlopen", return_value=empty):
            assert _raises(lambda: openrouter.chat("m", MESSAGES, 0.2)) == "empty reply"


def check_provider_switch() -> None:
    try:
        with mock.patch.dict(os.environ, {"TALK_PROVIDER": ""}):
            importlib.reload(client)
            assert client.PROVIDER == "ollama"
            assert client.MODEL_IN_USE == client.MODEL == "qwen3.5:9b"
            with mock.patch("backend.model.openrouter.chat") as hosted, \
                 mock.patch("ollama.chat", return_value={"message": {"content": "local"}}):
                assert client.send_chat(MESSAGES) == "local"
            hosted.assert_not_called()

        with mock.patch.dict(os.environ, {"TALK_PROVIDER": "OpenRouter"}):
            importlib.reload(client)
            assert client.PROVIDER == "openrouter"
            assert client.MODEL_IN_USE == client.OPENROUTER_MODEL == "qwen/qwen3.5-9b"
            with mock.patch("backend.model.openrouter.chat", return_value="hosted") as hosted, \
                 mock.patch("ollama.chat") as local:
                assert client.send_chat(MESSAGES) == "hosted"
            hosted.assert_called_once_with("qwen/qwen3.5-9b", MESSAGES, client.TEMPERATURE)
            local.assert_not_called()

        with mock.patch.dict(os.environ, {"TALK_PROVIDER": "openai"}):
            _raises(lambda: importlib.reload(client), ValueError)
    finally:
        # Leave the module as the real environment configures it.
        importlib.reload(client)


def main() -> None:
    check_openrouter()
    check_provider_switch()
    print("OK - openrouter.chat / TALK_PROVIDER switch")


if __name__ == "__main__":
    main()
