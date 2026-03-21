"""Wedding ceremony CRUD and ceremony script management."""

import csv
from pathlib import Path

from .db import get_connection


def add_ceremony(
    ceremony_date: str,
    partner_1_name: str,
    partner_2_name: str,
    ceremony_time: str = "",
    location: str = "",
    city: str = "",
    state: str = "",
    fee_charged: float = 0.0,
    script_used: str = "",
    notes: str = "",
) -> int:
    """Insert a new ceremony record and return the new row id."""
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO wedding_ceremonies
                (ceremony_date, ceremony_time, partner_1_name, partner_2_name,
                 location, city, state, fee_charged, script_used, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ceremony_date, ceremony_time, partner_1_name, partner_2_name,
             location, city, state, fee_charged, script_used, notes),
        )
        new_id = cur.lastrowid
    conn.close()
    return new_id


def get_ceremonies(search: str = "") -> list[dict]:
    """Return ceremonies as a list of dicts, newest first."""
    conn = get_connection()
    query = "SELECT * FROM wedding_ceremonies WHERE 1=1"
    params: list = []

    if search:
        like = f"%{search}%"
        query += " AND (partner_1_name LIKE ? OR partner_2_name LIKE ? OR location LIKE ? OR city LIKE ?)"
        params.extend([like, like, like, like])

    query += " ORDER BY ceremony_date DESC, created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def export_ceremonies_to_csv(output_path: str) -> str:
    """Export all ceremonies to CSV. Returns the output path."""
    ceremonies = get_ceremonies()
    if not ceremonies:
        return output_path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ceremonies[0].keys())
        writer.writeheader()
        writer.writerows(ceremonies)
    return output_path


# --- Ceremony Script Management ---

def save_script(name: str, text: str) -> None:
    """Insert or replace a ceremony script by name."""
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO ceremony_scripts (script_name, script_text) VALUES (?, ?) "
            "ON CONFLICT(script_name) DO UPDATE SET script_text = excluded.script_text",
            (name, text),
        )
    conn.close()


def get_all_scripts() -> list[dict]:
    """Return all ceremony scripts as a list of dicts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM ceremony_scripts ORDER BY script_name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_script_by_name(name: str) -> str:
    """Return script text for a given script name, or empty string if not found."""
    conn = get_connection()
    row = conn.execute(
        "SELECT script_text FROM ceremony_scripts WHERE script_name = ?", (name,)
    ).fetchone()
    conn.close()
    return row["script_text"] if row else ""


def delete_script(name: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM ceremony_scripts WHERE script_name = ?", (name,))
    conn.close()
