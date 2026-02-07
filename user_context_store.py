"""
Structured user context store (SQLite) for Phase 1.

Stores rules, preferences, and onboarding state under the extension's user_context/ workspace.
"""

import os
import sqlite3
import json
from typing import Any

# Will be set when used from __init__.py
_user_context_path: str | None = None


def set_user_context_path(path: str) -> None:
    """Set the root path for user context (user_context/ under extension)."""
    global _user_context_path
    _user_context_path = path


def get_user_context_path() -> str:
    """Return the user context root path; ensure dirs exist."""
    if _user_context_path is None:
        raise RuntimeError("user_context path not set; call set_user_context_path from __init__.py")
    return _user_context_path


def ensure_user_context_dirs() -> str:
    """Create user_context/ and user_context/skills/ if missing. Returns user_context path."""
    root = get_user_context_path()
    os.makedirs(os.path.join(root, "skills"), exist_ok=True)
    return root


def _get_db_path() -> str:
    return os.path.join(get_user_context_path(), "context.db")


def _get_conn() -> sqlite3.Connection:
    ensure_user_context_dirs()
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rule_text TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


def get_rules() -> list[dict[str, Any]]:
    """Return list of rules for prompt injection. Each dict: name, rule_text."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        cur = conn.execute("SELECT name, rule_text FROM rules ORDER BY id")
        return [{"name": row["name"], "rule_text": row["rule_text"]} for row in cur.fetchall()]
    finally:
        conn.close()


def get_preferences() -> dict[str, Any]:
    """Return preferences as key -> value (parsed JSON when applicable)."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        cur = conn.execute("SELECT key, value FROM preferences")
        out: dict[str, Any] = {}
        for row in cur.fetchall():
            key, value = row["key"], row["value"]
            if value is None:
                out[key] = None
            else:
                try:
                    out[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    out[key] = value
        return out
    finally:
        conn.close()


def get_onboarding_done() -> bool:
    """Return True if onboarding has been completed or skipped."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        cur = conn.execute("SELECT value FROM meta WHERE key = 'onboarding_done'")
        row = cur.fetchone()
        return row is not None and row["value"] in ("1", "true", "yes")
    finally:
        conn.close()


def set_onboarding_done() -> None:
    """Mark onboarding as done (after submit or skip)."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES ('onboarding_done', '1', datetime('now'))"
        )
        conn.commit()
    finally:
        conn.close()


def add_rule(name: str, rule_text: str) -> None:
    """Add a user rule."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        conn.execute("INSERT INTO rules (name, rule_text) VALUES (?, ?)", (name, rule_text))
        conn.commit()
    finally:
        conn.close()


def add_or_update_preference(key: str, value: Any) -> None:
    """Set a preference; value will be JSON-encoded if not a string."""
    conn = _get_conn()
    try:
        _init_schema(conn)
        if not isinstance(value, str):
            value = json.dumps(value)
        conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def save_onboarding(personality: str = "", goals: str = "", experience_level: str = "") -> None:
    """
    Persist onboarding answers: write SOUL.md, goals.md, set preferences and onboarding_done.
    Called by POST /api/user-context/onboarding. Empty strings are allowed (e.g. skip).
    """
    root = ensure_user_context_dirs()
    soul_path = os.path.join(root, "SOUL.md")
    goals_path = os.path.join(root, "goals.md")

    with open(soul_path, "w", encoding="utf-8") as f:
        f.write(personality.strip() or "# Personality\n\n(Not set. You can edit this file.)")

    goals_content = goals.strip()
    if experience_level:
        goals_content = (goals_content + "\n\n**Experience level**: " + experience_level).strip()
    if not goals_content:
        goals_content = "# Goals\n\n(Not set. You can edit this file.)"
    with open(goals_path, "w", encoding="utf-8") as f:
        f.write(goals_content)

    add_or_update_preference("experience_level", experience_level)
    set_onboarding_done()
