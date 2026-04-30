"""
Long-term memory store backed by SQLite.

Design:
- MemoryRecord is the domain model (Pydantic). Never pass raw dicts across boundaries.
- MemoryStore is the repository (Repository pattern): all SQL lives here, nowhere else.
- The LLM decides what to store and what to retrieve — we just provide the tools.
  This is Google's "Always On Memory Agent" pattern (2026): structured key-value facts,
  LLM-managed, no embeddings required.

Schema:
    memories(id, key, value, created_at, updated_at)

key   — a short label the LLM chooses (e.g. "user_name", "project_goal")
value — the fact to remember (free text)
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    id: int | None = None
    key: str
    value: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MemoryStore:
    """SQLite-backed repository for long-term memory facts.

    Single Responsibility: this class knows SQL; nothing else does.
    Dependency Inversion: consumers depend on MemoryStore's interface,
    not on sqlite3 directly.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT NOT NULL UNIQUE,
                value      TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def save(self, key: str, value: str) -> MemoryRecord:
        """Insert or update a memory by key (upsert)."""
        self._conn.execute("""
            INSERT INTO memories (key, value, created_at, updated_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                updated_at = datetime('now')
        """, (key, value))
        self._conn.commit()
        return self.get(key)  # type: ignore[return-value]

    def delete(self, key: str) -> bool:
        cursor = self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, key: str) -> MemoryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE key = ?", (key,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    def search(self, query: str) -> list[MemoryRecord]:
        """Full-text substring search across keys and values."""
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY updated_at DESC",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def all(self) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC"
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    # ------------------------------------------------------------------
    # Formatting helpers (used to inject memories into context)
    # ------------------------------------------------------------------

    def format_all(self) -> str:
        records = self.all()
        if not records:
            return "(no memories stored)"
        return "\n".join(f"- {r.key}: {r.value}" for r in records)

    def format_search(self, query: str) -> str:
        records = self.search(query)
        if not records:
            return f"(no memories matching '{query}')"
        return "\n".join(f"- {r.key}: {r.value}" for r in records)

    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            key=row["key"],
            value=row["value"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def close(self) -> None:
        self._conn.close()
