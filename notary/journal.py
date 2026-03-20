"""Notarial journal CRUD operations."""

import csv
from datetime import date
from pathlib import Path

from .db import get_connection


def add_entry(
    act_date: str,
    signer_name: str,
    act_type: str,
    act_time: str = "",
    document_type: str = "",
    id_type: str = "",
    id_number: str = "",
    num_signatures: int = 1,
    fee_charged: float = 0.0,
    travel_fee: float = 0.0,
    notes: str = "",
) -> int:
    """Insert a new journal entry and return the new row id."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO journal_entries
                (act_date, act_time, signer_name, document_type, act_type,
                 id_type, id_number, num_signatures, fee_charged, travel_fee, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (act_date, act_time, signer_name, document_type, act_type,
             id_type, id_number, num_signatures, fee_charged, travel_fee, notes),
        )
        new_id = cur.lastrowid
    conn.close()
    return new_id


def get_entries(
    search: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = 200,
) -> list[dict]:
    """Return journal entries as a list of dicts, newest first."""
    conn = get_connection()
    query = "SELECT * FROM journal_entries WHERE 1=1"
    params: list = []

    if search:
        query += " AND (signer_name LIKE ? OR document_type LIKE ? OR act_type LIKE ? OR notes LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if start_date:
        query += " AND act_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND act_date <= ?"
        params.append(end_date)

    query += " ORDER BY act_date DESC, created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_entry(entry_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.close()


def export_to_csv(output_path: str) -> str:
    """Export all journal entries to CSV. Returns the output path."""
    entries = get_entries(limit=100_000)
    if not entries:
        return output_path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=entries[0].keys())
        writer.writeheader()
        writer.writerows(entries)
    return output_path


def get_summary_stats() -> dict:
    """Return summary statistics for the journal."""
    conn = get_connection()
    current_year = date.today().year

    total_acts = conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]

    ytd_fees = conn.execute(
        "SELECT COALESCE(SUM(fee_charged + travel_fee), 0) FROM journal_entries WHERE strftime('%Y', act_date) = ?",
        (str(current_year),),
    ).fetchone()[0]

    acts_by_type = conn.execute(
        "SELECT act_type, COUNT(*) as count FROM journal_entries GROUP BY act_type ORDER BY count DESC"
    ).fetchall()

    conn.close()
    return {
        "total_acts": total_acts,
        "ytd_fees": round(ytd_fees, 2),
        "acts_by_type": {row["act_type"]: row["count"] for row in acts_by_type},
    }
