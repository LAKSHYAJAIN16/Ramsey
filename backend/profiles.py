"""SQLite-backed Ramsey profiles and progression.

OAuth identity is deliberately separate from cooking sessions: a visitor can
use Ramsey as a guest, while a signed-in cook gets durable progression.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from backend import config

PROFILE_DB_PATH = config.DATA_DIR / "ramsey.sqlite3"

RANKS = (
    (0, "Prep Cook"),
    (100, "Line Cook"),
    (300, "Sous Chef"),
    (700, "Chef de Partie"),
    (1400, "Head Chef"),
    (2500, "Kitchen Legend"),
)


def rank_for_xp(xp: int) -> str:
    return next(name for threshold, name in reversed(RANKS) if xp >= threshold)


class ProfileStore:
    def __init__(self, path: Path = PROFILE_DB_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS profiles (
                    google_sub TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT,
                    xp INTEGER NOT NULL DEFAULT 0,
                    calories INTEGER NOT NULL DEFAULT 0,
                    meals INTEGER NOT NULL DEFAULT 0,
                    streak INTEGER NOT NULL DEFAULT 0,
                    last_cooked_on TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def upsert_google_user(self, subject: str, email: str, display_name: str, avatar_url: Optional[str]) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO profiles (google_sub, email, display_name, avatar_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,
                    display_name=excluded.display_name, avatar_url=excluded.avatar_url, updated_at=excluded.updated_at""",
                (subject, email, display_name, avatar_url, now, now),
            )
        return self.get(subject)  # type: ignore[return-value]

    def get(self, subject: str) -> Optional[Dict]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM profiles WHERE google_sub = ?", (subject,)).fetchone()
        return self._serialize(row) if row else None

    def add_completed_meal(self, subject: str, calories: int) -> Optional[Dict]:
        profile = self.get(subject)
        if not profile:
            return None
        today = datetime.now(timezone.utc).date().isoformat()
        last = profile["last_cooked_on"]
        if last == today:
            streak = profile["streak"]
        else:
            yesterday = (datetime.now(timezone.utc).date().toordinal() - 1)
            expected = datetime.fromordinal(yesterday).date().isoformat()
            streak = profile["streak"] + 1 if last == expected else 1
        with self._connect() as connection:
            connection.execute(
                """UPDATE profiles SET xp=xp + 20, calories=calories + ?, meals=meals + 1,
                streak=?, last_cooked_on=?, updated_at=? WHERE google_sub=?""",
                (max(0, calories), streak, today, datetime.now(timezone.utc).isoformat(), subject),
            )
        return self.get(subject)

    @staticmethod
    def _serialize(row: sqlite3.Row) -> Dict:
        profile = dict(row)
        profile.pop("google_sub", None)
        profile["rank"] = rank_for_xp(profile["xp"])
        profile["level"] = profile["xp"] // 100 + 1
        return profile
