"""SQLite-backed provider configuration store."""

from __future__ import annotations

import base64
import os
import re
import sqlite3
from typing import Any

import user_context_store

_PROVIDER_TYPES = {'openai', 'anthropic', 'claude_code', 'codex', 'gemini_cli'}
_API_PROVIDERS = {'openai', 'anthropic'}
_CLI_PROVIDERS = {'claude_code', 'codex', 'gemini_cli'}
_NAME_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{1,62}$')


def _db_path() -> str:
    root = user_context_store.ensure_user_context_dirs()
    return os.path.join(root, 'providers.db')


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_providers_db() -> None:
    """Initialize providers.db and schema/triggers."""
    conn = _conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_type TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,

                api_key TEXT,
                base_url TEXT,
                model TEXT,

                max_tokens INTEGER,

                cli_command TEXT,
                cli_model TEXT,
                timeout_seconds INTEGER DEFAULT 180,

                is_active INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),

                CHECK (
                    (provider_type IN ('claude_code', 'codex', 'gemini_cli') AND name = provider_type)
                    OR
                    (provider_type IN ('openai', 'anthropic'))
                ),
                CHECK (is_active IN (0, 1))
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_providers_name ON providers(name);
            CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(is_active);
            CREATE INDEX IF NOT EXISTS idx_providers_type ON providers(provider_type);

            CREATE TRIGGER IF NOT EXISTS enforce_single_active_provider
            BEFORE UPDATE OF is_active ON providers
            WHEN NEW.is_active = 1
            BEGIN
                UPDATE providers SET is_active = 0 WHERE is_active = 1 AND id != NEW.id;
            END;

            CREATE TRIGGER IF NOT EXISTS enforce_single_active_provider_insert
            BEFORE INSERT ON providers
            WHEN NEW.is_active = 1
            BEGIN
                UPDATE providers SET is_active = 0 WHERE is_active = 1;
            END;
            """
        )
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def get_all_providers() -> list[dict[str, Any]]:
    init_providers_db()
    conn = _conn()
    try:
        rows = conn.execute(
            'SELECT * FROM providers ORDER BY created_at ASC, id ASC'
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_provider_by_name(name: str) -> dict[str, Any] | None:
    init_providers_db()
    conn = _conn()
    try:
        row = conn.execute(
            'SELECT * FROM providers WHERE name = ?', (name,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_active_provider() -> dict[str, Any] | None:
    init_providers_db()
    conn = _conn()
    try:
        row = conn.execute(
            'SELECT * FROM providers WHERE is_active = 1 ORDER BY id DESC LIMIT 1'
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def create_provider(data: dict[str, Any]) -> dict[str, Any]:
    init_providers_db()
    conn = _conn()
    try:
        conn.execute(
            """
            INSERT INTO providers (
                provider_type, name, display_name,
                api_key, base_url, model, max_tokens,
                cli_command, cli_model, timeout_seconds,
                is_active, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                data.get('provider_type'),
                data.get('name'),
                data.get('display_name'),
                data.get('api_key'),
                data.get('base_url'),
                data.get('model'),
                data.get('max_tokens'),
                data.get('cli_command'),
                data.get('cli_model'),
                int(data.get('timeout_seconds', 180) or 180),
                1 if data.get('is_active') else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    created = get_provider_by_name(str(data.get('name', '')))
    if created is None:
        raise RuntimeError('Failed to create provider')
    return created


def update_provider(name: str, data: dict[str, Any]) -> dict[str, Any]:
    init_providers_db()
    existing = get_provider_by_name(name)
    if existing is None:
        raise ValueError('Provider not found')

    merged = {**existing, **data}
    merged_name = merged.get('name') or name

    conn = _conn()
    try:
        conn.execute(
            """
            UPDATE providers
            SET provider_type = ?,
                name = ?,
                display_name = ?,
                api_key = ?,
                base_url = ?,
                model = ?,
                max_tokens = ?,
                cli_command = ?,
                cli_model = ?,
                timeout_seconds = ?,
                is_active = ?,
                updated_at = datetime('now')
            WHERE name = ?
            """,
            (
                merged.get('provider_type'),
                merged_name,
                merged.get('display_name'),
                merged.get('api_key'),
                merged.get('base_url'),
                merged.get('model'),
                merged.get('max_tokens'),
                merged.get('cli_command'),
                merged.get('cli_model'),
                int(merged.get('timeout_seconds', 180) or 180),
                1 if merged.get('is_active') else 0,
                name,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    updated = get_provider_by_name(str(merged_name))
    if updated is None:
        raise RuntimeError('Failed to update provider')
    return updated


def delete_provider(name: str) -> bool:
    init_providers_db()
    conn = _conn()
    try:
        cur = conn.execute('DELETE FROM providers WHERE name = ?', (name,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def set_active_provider(name: str) -> bool:
    init_providers_db()
    conn = _conn()
    try:
        row = conn.execute(
            'SELECT id FROM providers WHERE name = ?', (name,)
        ).fetchone()
        if row is None:
            return False
        conn.execute('UPDATE providers SET is_active = 0 WHERE is_active = 1')
        conn.execute(
            "UPDATE providers SET is_active = 1, updated_at = datetime('now') WHERE name = ?",
            (name,),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def encode_api_key(key: str) -> str:
    """Base64 encode API key string."""
    return base64.b64encode(key.encode('utf-8')).decode('ascii')


def decode_api_key(encoded: str) -> str:
    """Base64 decode API key string."""
    return base64.b64decode(encoded.encode('ascii')).decode('utf-8')


def _is_http_url(value: str) -> bool:
    return value.startswith('http://') or value.startswith('https://')


def validate_provider_config(
    provider_type: str, data: dict[str, Any]
) -> tuple[bool, str]:
    """Validate provider config payload."""
    if provider_type not in _PROVIDER_TYPES:
        return False, 'Invalid provider_type'

    name = str(data.get('name') or '').strip().lower()
    display_name = str(data.get('display_name') or '').strip()

    if not display_name:
        return False, 'display_name is required'

    if provider_type in _CLI_PROVIDERS:
        if name != provider_type:
            return False, 'CLI provider name must match provider_type'
        cli_command = str(data.get('cli_command') or '').strip()
        if not cli_command:
            return False, 'cli_command is required'
        if os.path.sep in cli_command:
            if not (os.path.isfile(cli_command) and os.access(cli_command, os.X_OK)):
                return False, 'cli_command path must exist and be executable'
        elif not _which(cli_command):
            return False, 'cli_command must be executable or available in PATH'
        timeout_seconds = data.get('timeout_seconds', 180)
        try:
            timeout_val = int(timeout_seconds)
        except (TypeError, ValueError):
            return False, 'timeout_seconds must be an integer'
        if timeout_val < 10 or timeout_val > 3600:
            return False, 'timeout_seconds must be between 10 and 3600'
        return True, ''

    if not name:
        return False, 'name is required'
    if not _NAME_RE.match(name):
        return False, 'name must match ^[a-z0-9][a-z0-9_-]{1,62}$'

    api_key = str(data.get('api_key') or '').strip()
    if not api_key:
        return False, 'api_key is required'
    if len(api_key) < 20:
        return False, 'api_key must be at least 20 characters'

    base_url = str(data.get('base_url') or '').strip()
    if base_url and not _is_http_url(base_url):
        return False, 'base_url must be a valid HTTP(S) URL'

    if provider_type == 'anthropic' and data.get('max_tokens') is not None:
        try:
            max_tokens = int(data.get('max_tokens'))
        except (TypeError, ValueError):
            return False, 'max_tokens must be an integer'
        if max_tokens < 64 or max_tokens > 32768:
            return False, 'max_tokens must be between 64 and 32768'

    return True, ''


def _which(command: str) -> str | None:
    for path in os.environ.get('PATH', '').split(os.pathsep):
        candidate = os.path.join(path, command)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None
