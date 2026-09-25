"""
The door between the browser and the rest of the backend.

requests_from_browser.py - gets each request from the browser (e.g.
                           "Send was pressed") and runs the right
                           function for it
answers_to_browser.py    - shapes the data sent back for the screen:
                           project, map tree, chat
activity_log.py          - the list of every saved change (Settings → Logs)
files_to_browser.py      - hands the browser the app's own files (HTML,
                           JavaScript, CSS) — not data

No product rules live here; those are in backend/project/.
"""
