import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("SQLITE_DB_PATH", "messages.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_name TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_dates (
                date TEXT PRIMARY KEY
            )
            """
        )


def insert_message(chat_name: str, sender: str, content: str, timestamp: int):
    created_at = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (chat_name, sender, content, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_name, sender, content, int(timestamp), created_at),
        )


def get_messages_for_date(date_str: str):
    start_dt = datetime.strptime(date_str, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT chat_name, sender, content, timestamp
            FROM messages
            WHERE timestamp >= ? AND timestamp < ?
            ORDER BY timestamp ASC
            """,
            (start_ts, end_ts),
        ).fetchall()
    return [dict(r) for r in rows]


def count_messages_for_date(date_str: str) -> int:
    start_dt = datetime.strptime(date_str, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE timestamp >= ? AND timestamp < ?",
            (start_ts, end_ts),
        ).fetchone()
    return int(row["count"])


def mark_date_processed(date_str: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_dates (date) VALUES (?)",
            (date_str,),
        )


def is_date_processed(date_str: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_dates WHERE date = ?",
            (date_str,),
        ).fetchone()
    return row is not None
