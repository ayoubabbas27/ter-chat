import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_SESSION_NAME_LEN = 56


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def database_path() -> Path:
    raw = os.getenv("DATABASE_PATH", "data/ter-chatbot.db")
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                messages TEXT NOT NULL DEFAULT '[]',
                code TEXT NOT NULL DEFAULT '',
                input_draft TEXT NOT NULL DEFAULT '',
                test_facts TEXT NOT NULL DEFAULT '[]',
                test_query TEXT NOT NULL DEFAULT '',
                test_history TEXT NOT NULL DEFAULT '[]',
                active_tab TEXT NOT NULL DEFAULT 'code'
            )
            """
        )
        conn.commit()


def normalize_session_name(name: str) -> str:
    cleaned = " ".join(str(name or "").split())
    if not cleaned:
        raise ValueError("Session name is required")
    if len(cleaned) <= MAX_SESSION_NAME_LEN:
        return cleaned
    return cleaned[: MAX_SESSION_NAME_LEN - 1].rstrip() + "…"


def _loads_json(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _row_to_session(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "messages": _loads_json(row["messages"], []),
        "code": row["code"] or "",
        "input_draft": row["input_draft"] or "",
        "test_facts": _loads_json(row["test_facts"], []),
        "test_query": row["test_query"] or "",
        "test_history": _loads_json(row["test_history"], []),
        "active_tab": row["active_tab"] if row["active_tab"] in ("code", "test") else "code",
    }


def list_sessions() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, created_at, updated_at
            FROM sessions
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_session(name: str) -> dict[str, Any]:
    session_name = normalize_session_name(name)
    session_id = uuid.uuid4().hex
    now = _utc_now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (
                id, name, created_at, updated_at,
                messages, code, input_draft, test_facts, test_query, test_history, active_tab
            ) VALUES (?, ?, ?, ?, '[]', '', '', '[]', '', '[]', 'code')
            """,
            (session_id, session_name, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise RuntimeError("Failed to create session")
    return _row_to_session(row)


def get_session(session_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        return None
    return _row_to_session(row)


def update_session(session_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_session(session_id)
    if existing is None:
        return None

    messages = payload.get("messages", existing["messages"])
    if not isinstance(messages, list):
        messages = existing["messages"]

    test_facts = payload.get("test_facts", existing["test_facts"])
    if not isinstance(test_facts, list):
        test_facts = existing["test_facts"]

    test_history = payload.get("test_history", existing["test_history"])
    if not isinstance(test_history, list):
        test_history = existing["test_history"]

    active_tab = payload.get("active_tab", existing["active_tab"])
    if active_tab not in ("code", "test"):
        active_tab = "code"

    name = existing["name"]
    now = _utc_now()

    with connect() as conn:
        conn.execute(
            """
            UPDATE sessions SET
                name = ?,
                updated_at = ?,
                messages = ?,
                code = ?,
                input_draft = ?,
                test_facts = ?,
                test_query = ?,
                test_history = ?,
                active_tab = ?
            WHERE id = ?
            """,
            (
                name,
                now,
                json.dumps(messages, ensure_ascii=False),
                str(payload.get("code", existing["code"]) or ""),
                str(payload.get("input_draft", existing["input_draft"]) or ""),
                json.dumps(test_facts, ensure_ascii=False),
                str(payload.get("test_query", existing["test_query"]) or ""),
                json.dumps(test_history, ensure_ascii=False),
                active_tab,
                session_id,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()

    if row is None:
        return None
    return _row_to_session(row)


def delete_session(session_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0
