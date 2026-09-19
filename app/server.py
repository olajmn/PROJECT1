"""
HTTP process entry for app/ — starts the server that serves ui/ and
backend.api routes.

API shapes and handlers live in backend/api/ (views.py, routes.py,
state.py). This file only binds the port.

Run from app/ (this directory), with app/'s own venv:
    .venv/bin/python server.py
Then open http://localhost:8000/ in a browser.
"""

from http.server import ThreadingHTTPServer

from backend.api.routes import Handler, PORT


if __name__ == "__main__":
    print(f"web prototype - http://localhost:{PORT}/")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
