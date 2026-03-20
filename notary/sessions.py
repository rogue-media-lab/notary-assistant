"""Chat session save/retrieve operations."""

from .db import get_connection


def save_session(
    label: str,
    transcript: str,
    summary: str = "",
    journal_entry_id: int | None = None,
) -> int:
    """Save a chat session and return the new row id."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO chat_sessions (label, summary, transcript, journal_entry_id)
            VALUES (?, ?, ?, ?)
            """,
            (label, summary, transcript, journal_entry_id),
        )
        new_id = cur.lastrowid
    conn.close()
    return new_id


def get_sessions() -> list[dict]:
    """Return all saved sessions, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, created_at, label, summary, journal_entry_id FROM chat_sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id: int) -> dict | None:
    """Return a single session including the full transcript."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(session_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.close()
