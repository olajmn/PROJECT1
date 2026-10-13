"""
HTTP process entry for app/ — starts the server that serves ui/ and
backend.api routes.

What each request does lives in backend/api/ (requests_from_browser.py,
answers_to_browser.py). This file only starts the server.

Run from app/ (this directory), with app/'s own venv:
    .venv/bin/python -m server
Then open http://localhost:8000/ in a browser.

HOST is localhost unless set: only this machine can connect. A host
running the public demo sets HOST=0.0.0.0 behind its HTTPS proxy
(docs/demo.md).
"""

import os
from http.server import ThreadingHTTPServer

from backend.api.requests_from_browser import Handler, PORT

HOST = os.environ.get("HOST", "localhost")


if __name__ == "__main__":
    print(f"web prototype - http://{HOST}:{PORT}/")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
