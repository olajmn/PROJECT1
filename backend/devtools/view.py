"""
A simple, static HTML view of your saved goals/plans history.

This is NOT the product's frontend - it's a personal debugging/
understanding tool, generated fresh each time you run it. No server, no
JavaScript, just a plain HTML file you open in a browser. See
docs/09-mvp.md § Testing philosophy for why the real frontend is
deliberately not being built yet.

Run from the PROJECT ROOT: .venv/bin/python -m backend.devtools.view
"""

import webbrowser

from backend.storage import DATA_DIR, load_history

OUTPUT_FILE = DATA_DIR / "view.html"


def render_html(history: list[dict]) -> str:
    """Turn the saved history into a simple HTML page."""
    if not history:
        cards = "<p>No plans saved yet. Run goal_to_plan.py first.</p>"
    else:
        # Newest first, so the most recent goal is at the top
        cards = "\n".join(_render_card(record) for record in reversed(history))

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Agent history</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 700px;
          margin: 40px auto; padding: 0 20px; color: #222; }}
  h1 {{ font-size: 1.4rem; }}
  .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px;
           margin-bottom: 20px; }}
  .goal {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }}
  .timestamp {{ color: #888; font-size: 0.85rem; margin-bottom: 12px; }}
  .horizon {{ margin-bottom: 8px; }}
  .horizon-label {{ font-weight: 600; color: #555; }}
  .right-now {{ background: #eef6ff; border-left: 3px solid #3b82f6;
                padding: 8px 12px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>Agent history ({len(history)} entr{"y" if len(history) == 1 else "ies"})</h1>
{cards}
</body>
</html>
"""


def _render_card(record: dict) -> str:
    plan = record["plan"]

    # Backwards compatibility: entries saved before the switch to
    # structured JSON output (v0.1) have `plan` as a plain string,
    # not a dict. Show them as-is instead of crashing.
    if isinstance(plan, str):
        return f"""<div class="card">
  <div class="goal">#{record['id']} — {record['goal']}</div>
  <div class="timestamp">{record['created_at']} (old free-text format)</div>
  <div>{plan}</div>
</div>"""

    horizons = ""
    for key, label in [
        ("one_year", "1 year"),
        ("one_month", "1 month"),
        ("this_week", "This week"),
    ]:
        if key in plan:
            horizons += (
                f'<div class="horizon"><span class="horizon-label">'
                f"{label}:</span> {plan[key]}</div>\n"
            )

    right_now = plan.get("right_now", "")

    return f"""<div class="card">
  <div class="goal">#{record['id']} — {record['goal']}</div>
  <div class="timestamp">{record['created_at']}</div>
  {horizons}
  <div class="right-now"><strong>Right now:</strong> {right_now}</div>
</div>"""


if __name__ == "__main__":
    history = load_history()
    html = render_html(history)

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")

    print(f"Wrote {OUTPUT_FILE}")
    webbrowser.open(f"file://{OUTPUT_FILE.resolve()}")
