"""Persistent scan snapshots and account-change analytics."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class HistoryStore:
    def __init__(self, database_path: str | Path = "data/instareciprocal.db") -> None:
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imported_at TEXT NOT NULL UNIQUE,
                    scanned_at TEXT NOT NULL,
                    followers_count INTEGER NOT NULL,
                    following_count INTEGER NOT NULL,
                    mutual_count INTEGER NOT NULL,
                    not_following_back_count INTEGER NOT NULL,
                    followers_json TEXT NOT NULL,
                    following_json TEXT NOT NULL,
                    not_following_back_json TEXT NOT NULL
                )
            """)

    def save_snapshot(self, imported_at: str, followers: list[str],
                      following: list[str], not_following_back: list[str]) -> bool:
        """Save once per source export timestamp. Return False if already saved."""
        timestamp = datetime.now(timezone.utc).isoformat()
        followers_set = sorted(set(followers))
        following_set = sorted(set(following))
        not_back_set = sorted(set(not_following_back))
        with sqlite3.connect(self.database_path) as db:
            cursor = db.execute("""
                INSERT OR IGNORE INTO scan_history (
                    imported_at, scanned_at, followers_count, following_count,
                    mutual_count, not_following_back_count, followers_json,
                    following_json, not_following_back_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                imported_at, timestamp, len(followers_set), len(following_set),
                len(set(followers_set) & set(following_set)),
                len(not_back_set), json.dumps(followers_set),
                json.dumps(following_set), json.dumps(not_back_set),
            ))
            return cursor.rowcount == 1

    def list_snapshots(self) -> list[dict]:
        with sqlite3.connect(self.database_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("""
                SELECT id, imported_at, scanned_at, followers_count,
                       following_count, mutual_count, not_following_back_count
                FROM scan_history ORDER BY id DESC
            """).fetchall()
        return [dict(row) for row in rows]

    def get_snapshot(self, snapshot_id: int) -> dict | None:
        with sqlite3.connect(self.database_path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "SELECT * FROM scan_history WHERE id = ?", (snapshot_id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        for key in ("followers", "following", "not_following_back"):
            data[key] = json.loads(data.pop(f"{key}_json"))
        return data

    def compare_latest(self) -> dict | None:
        snapshots = self.list_snapshots()
        if len(snapshots) < 2:
            return None
        current = self.get_snapshot(snapshots[0]["id"])
        previous = self.get_snapshot(snapshots[1]["id"])
        assert current is not None and previous is not None
        return {
            "current_scan": current["imported_at"],
            "previous_scan": previous["imported_at"],
            "new_followers": sorted(set(current["followers"]) - set(previous["followers"])),
            "lost_followers": sorted(set(previous["followers"]) - set(current["followers"])),
            "new_following": sorted(set(current["following"]) - set(previous["following"])),
            "no_longer_following": sorted(set(previous["following"]) - set(current["following"])),
            "new_non_followers": sorted(
                set(current["not_following_back"]) - set(previous["not_following_back"])
            ),
            "no_longer_non_followers": sorted(
                set(previous["not_following_back"]) - set(current["not_following_back"])
            ),
        }
