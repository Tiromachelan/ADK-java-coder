"""Flask web app for browsing the ADK Java Coder explanation database.

Run with:
    python web/app.py

Then open http://localhost:5000 in your browser.
"""

import html
import sqlite3
from pathlib import Path

from flask import Flask, abort, redirect, url_for

DB_PATH = Path(__file__).parent.parent / "explanations.db"

app = Flask(__name__)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Shared HTML layout
# ---------------------------------------------------------------------------

_CSS = """
<style>
  body { font-family: system-ui, sans-serif; margin: 0; background: #f5f5f5; color: #222; }
  .container { max-width: 960px; margin: 0 auto; padding: 1.5rem 2rem; }
  h1 { color: #1a1a2e; }
  h2 { color: #16213e; border-bottom: 2px solid #e0e0e0; padding-bottom: .4rem; }
  h3 { color: #0f3460; margin-bottom: .25rem; }
  a { color: #e94560; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1);
          padding: 1rem 1.25rem; margin-bottom: 1rem; }
  .badge { display: inline-block; border-radius: 4px; padding: 2px 8px;
           font-size: .75rem; font-weight: 600; margin-right: 4px; }
  .badge-modularization { background: #dbeafe; color: #1d4ed8; }
  .badge-data_structure { background: #dcfce7; color: #15803d; }
  .badge-test_design    { background: #fef9c3; color: #854d0e; }
  .badge-code_fix       { background: #fee2e2; color: #b91c1c; }
  .badge-unknown        { background: #e5e7eb; color: #374151; }
  .meta { font-size: .8rem; color: #666; margin-bottom: .5rem; }
  .context-box { background: #1e1e2e; color: #cdd6f4; border-radius: 6px;
                 padding: .75rem 1rem; font-family: monospace; font-size: .8rem;
                 white-space: pre-wrap; overflow-x: auto; margin-top: .5rem; }
  .diff-box { background: #0d1117; color: #e6edf3; border-radius: 6px;
              padding: .75rem 1rem; font-family: monospace; font-size: .75rem;
              white-space: pre; overflow-x: auto; margin-top: .5rem; line-height: 1.5; }
  .diff-add  { color: #3fb950; }
  .diff-rem  { color: #f85149; }
  .diff-hunk { color: #58a6ff; }
  .files-list { margin: .4rem 0; padding-left: 1.2rem; }
  .nav { background: #1a1a2e; padding: .75rem 2rem; }
  .nav a { color: #e94560; font-weight: 600; margin-right: 1.5rem; }
  .empty { color: #888; font-style: italic; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #e5e7eb; }
  th { background: #f9fafb; font-size: .85rem; color: #555; }
  tr:hover td { background: #fafafa; }
</style>
"""


def _layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{html.escape(title)} — Java Coder Explanations</title>{_CSS}</head>
<body>
<div class="nav">
  <a href="/">🏠 Sessions</a>
</div>
<div class="container">
  <h1>{html.escape(title)}</h1>
  {body}
</div>
</body>
</html>"""


def _badge(decision_type: str) -> str:
    safe = html.escape(decision_type or "unknown")
    cls = safe if safe in ("modularization", "data_structure", "test_design", "code_fix") else "unknown"
    return f'<span class="badge badge-{cls}">{safe}</span>'


def _render_diff(diff_text: str) -> str:
    if not diff_text:
        return ""
    lines_html = []
    for line in diff_text.splitlines():
        escaped = html.escape(line)
        if line.startswith("@@"):
            lines_html.append(f'<span class="diff-hunk">{escaped}</span>')
        elif line.startswith("+") and not line.startswith("+++"):
            lines_html.append(f'<span class="diff-add">{escaped}</span>')
        elif line.startswith("-") and not line.startswith("---"):
            lines_html.append(f'<span class="diff-rem">{escaped}</span>')
        else:
            lines_html.append(escaped)
    return '<div class="diff-box">' + "\n".join(lines_html) + "</div>"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if not DB_PATH.exists():
        body = '<p class="empty">No explanations database found yet. Run <code>python main.py</code> first.</p>'
        return _layout("Sessions", body)

    with _get_db() as conn:
        rows = conn.execute("""
            SELECT s.id, s.task, s.started_at,
                   COUNT(DISTINCT e.id) AS explanation_count,
                   MAX(e.cycle) AS max_cycle
            FROM sessions s
            LEFT JOIN explanations e ON e.session_id = s.id
            GROUP BY s.id
            ORDER BY s.started_at DESC
        """).fetchall()

    if not rows:
        body = '<p class="empty">No sessions recorded yet.</p>'
        return _layout("Sessions", body)

    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
          <td><a href="/session/{html.escape(r['id'])}">{html.escape(r['id'][:12])}…</a></td>
          <td>{html.escape(r['task'])}</td>
          <td>{r['explanation_count']}</td>
          <td>{r['max_cycle'] or 0}</td>
          <td>{html.escape(r['started_at'] or '')}</td>
        </tr>"""

    body = f"""
    <table>
      <thead><tr><th>Session ID</th><th>Task</th><th>Explanations</th><th>TDD Cycles</th><th>Started</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>"""
    return _layout("Sessions", body)


@app.route("/session/<session_id>")
def session_detail(session_id: str):
    if not DB_PATH.exists():
        abort(404)

    with _get_db() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not session:
            abort(404)

        explanations = conn.execute("""
            SELECT e.*, GROUP_CONCAT(fc.filename, ', ') AS filenames
            FROM explanations e
            LEFT JOIN file_changes fc ON fc.explanation_id = e.id
            WHERE e.session_id = ?
            GROUP BY e.id
            ORDER BY e.cycle, e.id
        """, (session_id,)).fetchall()

    # Group by cycle
    cycles: dict[int, list] = {}
    for exp in explanations:
        cycles.setdefault(exp["cycle"], []).append(exp)

    body = f'<p class="meta">Task: <strong>{html.escape(session["task"])}</strong> &nbsp;|&nbsp; Started: {html.escape(session["started_at"] or "")}</p>'

    if not cycles:
        body += '<p class="empty">No explanations recorded for this session.</p>'
        return _layout(f"Session {session_id[:12]}", body)

    for cycle_num in sorted(cycles.keys()):
        label = "Initial Version" if cycle_num == 0 else f"TDD Cycle {cycle_num}"
        body += f"<h2>{label}</h2>"
        for exp in cycles[cycle_num]:
            files_html = ""
            if exp["filenames"]:
                files_html = f'<p class="meta">Files: <code>{html.escape(exp["filenames"])}</code></p>'
            body += f"""
            <div class="card">
              <h3><a href="/explanation/{exp['id']}">{_badge(exp['decision_type'])}{html.escape(exp['agent'])}</a></h3>
              <p class="meta">#{exp['id']} &nbsp;|&nbsp; {html.escape(exp['created_at'] or '')}</p>
              {files_html}
              <p>{html.escape(exp['reasoning'])}</p>
            </div>"""

    return _layout(f"Session {session_id[:12]}", body)


@app.route("/explanation/<int:explanation_id>")
def explanation_detail(explanation_id: int):
    if not DB_PATH.exists():
        abort(404)

    with _get_db() as conn:
        exp = conn.execute(
            "SELECT * FROM explanations WHERE id = ?", (explanation_id,)
        ).fetchone()
        if not exp:
            abort(404)

        changes = conn.execute(
            "SELECT * FROM file_changes WHERE explanation_id = ?", (explanation_id,)
        ).fetchall()

        session = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (exp["session_id"],)
        ).fetchone()

    cycle_label = "Initial Version" if exp["cycle"] == 0 else f"TDD Cycle {exp['cycle']}"
    session_link = f'<a href="/session/{html.escape(exp["session_id"])}">{html.escape(exp["session_id"][:12])}…</a>'

    context_html = ""
    if exp["context"]:
        context_html = f'<h3>Context (error / trigger)</h3><div class="context-box">{html.escape(exp["context"])}</div>'

    changes_html = ""
    for fc in changes:
        diff_html = _render_diff(fc["diff"])
        changes_html += f"""
        <div class="card">
          <h3>{html.escape(fc['filename'])} <span class="badge badge-{'modularization' if fc['change_type']=='created' else 'code_fix'}">{html.escape(fc['change_type'])}</span></h3>
          <p class="meta">+{fc['lines_added']} lines added &nbsp;/&nbsp; -{fc['lines_removed']} lines removed</p>
          {diff_html}
        </div>"""

    body = f"""
    <p class="meta">{_badge(exp['decision_type'])} &nbsp; Agent: <strong>{html.escape(exp['agent'])}</strong>
       &nbsp;|&nbsp; {cycle_label}
       &nbsp;|&nbsp; Session: {session_link}
       &nbsp;|&nbsp; {html.escape(exp['created_at'] or '')}
    </p>
    <h2>Reasoning</h2>
    <div class="card"><p>{html.escape(exp['reasoning'])}</p></div>
    {context_html}
    {'<h2>File Changes</h2>' + changes_html if changes_html else '<p class="empty">No file changes recorded.</p>'}
    """
    return _layout(f"Explanation #{explanation_id}", body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Explanation DB: {DB_PATH}")
    print("Starting web server → http://localhost:5000")
    app.run(debug=True, port=5000)
