"""Persistent local review decisions backed by SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUSES = {"pending", "reviewed", "skipped", "unfollowed_manually"}


class ReviewStore:
    def __init__(self, database_path: str | Path = "data/instareciprocal.db") -> None:
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS review_decisions (
                    username TEXT PRIMARY KEY COLLATE NOCASE,
                    status TEXT NOT NULL DEFAULT 'pending',
                    note TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS review_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL COLLATE NOCASE,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)

    @staticmethod
    def _normalize(username: str) -> str:
        value = username.strip().lstrip("@").lower()
        if not value:
            raise ValueError("Username cannot be empty.")
        return value

    def get_status(self, username: str) -> str:
        name = self._normalize(username)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT status FROM review_decisions WHERE username = ?", (name,)
            ).fetchone()
        return row["status"] if row else "pending"

    def set_status(self, username: str, status: str, note: str = "") -> None:
        name = self._normalize(username)
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid review status: {status}")
        timestamp = datetime.now(timezone.utc).isoformat()
        clean_note = note.strip()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT status FROM review_decisions WHERE username = ?", (name,)
            ).fetchone()
            old_status = row["status"] if row else None
            connection.execute("""
                INSERT INTO review_decisions (username, status, note, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    status = excluded.status,
                    note = excluded.note,
                    updated_at = excluded.updated_at
            """, (name, status, clean_note, timestamp))
            connection.execute("""
                INSERT INTO review_events
                    (username, old_status, new_status, note, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, old_status, status, clean_note, timestamp))

    def get_all(self) -> dict[str, dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT username, status, note, updated_at
                FROM review_decisions ORDER BY username COLLATE NOCASE
            """).fetchall()
        return {
            row["username"]: {
                "status": row["status"],
                "note": row["note"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    def get_history(self, username: str | None = None) -> list[dict[str, str | None]]:
        with self._connect() as connection:
            if username:
                rows = connection.execute("""
                    SELECT username, old_status, new_status, note, created_at
                    FROM review_events WHERE username = ?
                    ORDER BY id DESC
                """, (self._normalize(username),)).fetchall()
            else:
                rows = connection.execute("""
                    SELECT username, old_status, new_status, note, created_at
                    FROM review_events ORDER BY id DESC
                """).fetchall()
        return [dict(row) for row in rows]

    def status_counts(self) -> dict[str, int]:
        counts = {status: 0 for status in VALID_STATUSES}
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT status, COUNT(*) AS total
                FROM review_decisions GROUP BY status
            """).fetchall()
        counts.update({row["status"]: row["total"] for row in rows})
        return counts
