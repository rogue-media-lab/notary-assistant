"""SQLite connection helper and schema initialization."""

import sqlite3
from pathlib import Path

from . import config as cfg

DB_FILE = cfg.CONFIG_DIR / "notary.db"

DEFAULT_CEREMONY_SCRIPT = """\
Dearly beloved, we are gathered here today to celebrate the union of {partner_1} and {partner_2}.

Marriage is a sacred commitment — a promise to love, support, and cherish one another through all of life's seasons.

{partner_1}, do you take {partner_2} to be your lawfully wedded spouse, to have and to hold, from this day forward, for better, for worse, for richer, for poorer, in sickness and in health, to love and to cherish, until death do you part?

(Response: I do.)

{partner_2}, do you take {partner_1} to be your lawfully wedded spouse, to have and to hold, from this day forward, for better, for worse, for richer, for poorer, in sickness and in health, to love and to cherish, until death do you part?

(Response: I do.)

By the power vested in me as a Notary Public of the State of South Carolina, I now pronounce you married.

You may kiss!

Ladies and gentlemen, it is my honor to present the newly married couple!
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_schema() -> None:
    """Create all tables if they do not exist and seed default data."""
    cfg.ensure_dirs()
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                act_date        TEXT NOT NULL,
                act_time        TEXT,
                signer_name     TEXT NOT NULL,
                document_type   TEXT,
                act_type        TEXT NOT NULL,
                id_type         TEXT,
                id_number       TEXT,
                num_signatures  INTEGER DEFAULT 1,
                fee_charged     REAL DEFAULT 0.0,
                travel_fee      REAL DEFAULT 0.0,
                notes           TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS wedding_ceremonies (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                ceremony_date   TEXT NOT NULL,
                ceremony_time   TEXT,
                partner_1_name  TEXT NOT NULL,
                partner_2_name  TEXT NOT NULL,
                location        TEXT,
                city            TEXT,
                state           TEXT DEFAULT 'SC',
                fee_charged     REAL DEFAULT 0.0,
                script_used     TEXT,
                notes           TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ceremony_scripts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                script_name TEXT NOT NULL UNIQUE,
                script_text TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS checklist_records (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at        TEXT NOT NULL DEFAULT (datetime('now')),
                record_date       TEXT NOT NULL,
                client_name       TEXT NOT NULL,
                document_type     TEXT,
                items_checked     INTEGER NOT NULL,
                total_items       INTEGER NOT NULL,
                journal_entry_id  INTEGER,
                notes             TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at        TEXT NOT NULL DEFAULT (datetime('now')),
                label             TEXT NOT NULL,
                summary           TEXT,
                transcript        TEXT NOT NULL,
                journal_entry_id  INTEGER
            )
        """)

        # Seed default script if none exist
        count = conn.execute("SELECT COUNT(*) FROM ceremony_scripts").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO ceremony_scripts (script_name, script_text) VALUES (?, ?)",
                ("Default Ceremony Script", DEFAULT_CEREMONY_SCRIPT),
            )
    conn.close()
