"""SQLite-backed explanation logger for the ADK Java Coder pipeline.

All tool functions in this module are exposed as ADK FunctionTools to agents.
Module-level state tracks the current session_id and cycle counter so agents
don't need to pass them explicitly.
"""

import difflib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from tools.shell_tools import WORKSPACE, write_file as _write_file

DB_PATH = Path(__file__).parent.parent / "explanations.db"

# Module-level session state — set by init_session() in main.py
_current_session_id: str = "unknown"
_current_task: str = ""
_current_cycle: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            task        TEXT NOT NULL,
            started_at  DATETIME DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS explanations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL REFERENCES sessions(id),
            cycle         INTEGER NOT NULL DEFAULT 0,
            agent         TEXT    NOT NULL,
            decision_type TEXT    NOT NULL,
            context       TEXT,
            reasoning     TEXT    NOT NULL,
            created_at    DATETIME DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS file_changes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            explanation_id INTEGER NOT NULL REFERENCES explanations(id),
            filename       TEXT    NOT NULL,
            change_type    TEXT    NOT NULL,
            lines_added    INTEGER NOT NULL DEFAULT 0,
            lines_removed  INTEGER NOT NULL DEFAULT 0,
            diff           TEXT
        );
    """)
    conn.commit()


def _compute_diff(filename: str, new_content: str) -> tuple[str, int, int, str]:
    """Return (change_type, lines_added, lines_removed, diff_text)."""
    target = WORKSPACE / filename
    if not target.exists():
        lines_added = len(new_content.splitlines())
        return "created", lines_added, 0, new_content

    old_content = target.read_text(encoding="utf-8")
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))
    diff_text = "".join(diff_lines)

    lines_added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    lines_removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

    return "modified", lines_added, lines_removed, diff_text


# ---------------------------------------------------------------------------
# Session / cycle management (called from main.py and pipeline agents)
# ---------------------------------------------------------------------------

def init_session(session_id: str, task: str) -> None:
    """Register a new coding session. Called once from main.py before the runner starts."""
    global _current_session_id, _current_task, _current_cycle
    _current_session_id = session_id
    _current_task = task
    _current_cycle = 0

    with _get_connection() as conn:
        _ensure_schema(conn)
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, task) VALUES (?, ?)",
            (session_id, task),
        )
        conn.commit()


def increment_cycle() -> str:
    """Increment the TDD cycle counter. Called by CycleTrackerAgent at the start of each loop.

    Returns:
        Confirmation string with the new cycle number.
    """
    global _current_cycle
    _current_cycle += 1
    return f"Cycle counter incremented to {_current_cycle}."


# ---------------------------------------------------------------------------
# Logging tools exposed to agents as FunctionTools
# ---------------------------------------------------------------------------

def log_explanation(
    decision_type: str,
    reasoning: str,
    context: str = "",
    files_affected: str = "",
    agent: str = "",
) -> str:
    """Log a design or architectural explanation to the database (no file write).

    Use this for modularization and data structure decisions where no file
    content change needs to be recorded (e.g., after calling write_file for
    several files and you want to explain the overall design choices).

    Args:
        decision_type: One of 'modularization', 'data_structure', 'test_design', 'code_fix'.
        reasoning: The explanation of the decision (why this design was chosen).
        context: The error or instruction that prompted this decision (empty for first_version).
        files_affected: Comma-separated list of filenames involved (e.g. 'Calculator.java,MathUtils.java').
        agent: The name of the agent logging this (auto-detected if blank).

    Returns:
        Confirmation string with the new explanation id.
    """
    agent_name = agent or "unknown"
    with _get_connection() as conn:
        _ensure_schema(conn)
        cur = conn.execute(
            """INSERT INTO explanations (session_id, cycle, agent, decision_type, context, reasoning)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_current_session_id, _current_cycle, agent_name, decision_type, context, reasoning),
        )
        explanation_id = cur.lastrowid

        if files_affected:
            for fname in [f.strip() for f in files_affected.split(",") if f.strip()]:
                target = WORKSPACE / fname
                change_type = "created" if not target.exists() else "modified"
                conn.execute(
                    """INSERT INTO file_changes (explanation_id, filename, change_type, lines_added, lines_removed, diff)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (explanation_id, fname, change_type, 0, 0, ""),
                )
        conn.commit()

    return f"Explanation logged (id={explanation_id}, session={_current_session_id}, cycle={_current_cycle})."


def write_file_explained(
    filename: str,
    content: str,
    decision_type: str,
    reasoning: str,
    context: str = "",
    agent: str = "",
) -> str:
    """Write a Java file to workspace/ AND log an explanation with a line-level diff.

    Use this instead of write_file when you want to record WHY the file was
    created or changed (e.g., fixing a compilation error, addressing a test failure).

    Args:
        filename: Relative path inside workspace/ (e.g. 'Calculator.java').
        content: Full text content to write.
        decision_type: One of 'modularization', 'data_structure', 'test_design', 'code_fix'.
        reasoning: Explanation of what changed and why.
        context: The error or failure message that triggered this change (empty for new files).
        agent: The name of the agent writing (auto-detected if blank).

    Returns:
        Confirmation string with the write result and explanation id.
    """
    change_type, lines_added, lines_removed, diff_text = _compute_diff(filename, content)
    write_result = _write_file(filename, content)

    agent_name = agent or "unknown"
    with _get_connection() as conn:
        _ensure_schema(conn)
        cur = conn.execute(
            """INSERT INTO explanations (session_id, cycle, agent, decision_type, context, reasoning)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_current_session_id, _current_cycle, agent_name, decision_type, context, reasoning),
        )
        explanation_id = cur.lastrowid
        conn.execute(
            """INSERT INTO file_changes (explanation_id, filename, change_type, lines_added, lines_removed, diff)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (explanation_id, filename, change_type, lines_added, lines_removed, diff_text),
        )
        conn.commit()

    return (
        f"{write_result} | "
        f"Explanation logged (id={explanation_id}, {change_type}, "
        f"+{lines_added}/-{lines_removed} lines)."
    )
