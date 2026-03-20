"""Checklist record save/retrieve operations."""

from .db import get_connection


def save_record(
    record_date: str,
    client_name: str,
    items_checked: int,
    total_items: int,
    document_type: str = "",
    journal_entry_id: int | None = None,
    notes: str = "",
) -> int:
    """Save a completed checklist record and return the new row id."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO checklist_records
                (record_date, client_name, document_type, items_checked, total_items,
                 journal_entry_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (record_date, client_name, document_type, items_checked, total_items,
             journal_entry_id, notes),
        )
        new_id = cur.lastrowid
    conn.close()
    return new_id


def get_records(search: str = "") -> list[dict]:
    """Return checklist records newest first, with optional name search."""
    conn = get_connection()
    query = "SELECT * FROM checklist_records WHERE 1=1"
    params: list = []
    if search:
        like = f"%{search}%"
        query += " AND (client_name LIKE ? OR document_type LIKE ?)"
        params.extend([like, like])
    query += " ORDER BY record_date DESC, created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_record(record_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM checklist_records WHERE id = ?", (record_id,))
    conn.close()
