"""
OpenRouter's chat API, the hosted model for the public demo only
(docs/05-decisions.md #70). Same contract as model.client.send_chat():
a whole chat in, raw reply text out. model.client decides whether this
is used and which model it asks for.

The API key is read from OPENROUTER_API_KEY when a call is made. It is
never logged or put in an error: errors carry a status or an error type
only, because the API layer prints them to the server terminal.
"""

import json
import os
import urllib.error
import urllib.request

URL = "https://openrouter.ai/api/v1/chat/completions"

# Replies are one to four sentences (talk_prompt.py); this leaves room
# for a long one and bounds what a single call can cost.
MAX_TOKENS = 400

# A hung call must not hold a server thread forever.
TIMEOUT_SECONDS = 60


class OpenRouterError(RuntimeError):
    """A failed call, described without the key or the response body."""


def chat(model: str, messages: list[dict], temperature: float) -> str:
    """Send `messages` ([{role, content}]) to `model` with reasoning off,
    the same as think=False on Ollama, and return the reply text."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": MAX_TOKENS,
        "reasoning": {"enabled": False},
    }).encode("utf-8")
    request = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as e:
        raise OpenRouterError(f"HTTP {e.code}") from None
    except OSError as e:  # unreachable, refused, timed out
        raise OpenRouterError(f"request failed: {type(e).__name__}") from None
    except json.JSONDecodeError:
        raise OpenRouterError("response was not JSON") from None
    # An upstream failure can arrive as HTTP 200 with an "error" body
    # and no choices.
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise OpenRouterError("no reply in response") from None
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("empty reply")
    return content
