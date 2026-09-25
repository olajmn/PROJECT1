"""
HTTP process entry for app/ — starts the server that serves ui/ and
backend.api routes.

What each request does lives in backend/api/ (requests_from_browser.py,
answers_to_browser.py). This file only starts the server.

Run from app/ (this directory), with app/'s own venv:
    .venv/bin/python server.py
Then open http://localhost:8000/ in a browser.
"""

from http.server import ThreadingHTTPServer

from backend.api.requests_from_browser import Handler, PORT


if __name__ == "__main__":
    print(f"web prototype - http://localhost:{PORT}/")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
