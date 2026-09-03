"""SQLite konuşma geçmişi veri erişim katmanı."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HistoryDatabase:
    """Her işlemde kısa ömürlü bağlantı kullanan SQLite deposu."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _serialize(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        record = dict(row)
        record["is_favorite"] = bool(record["is_favorite"])
        return record

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    preset TEXT NOT NULL,
                    exaggeration REAL NOT NULL,
                    cfg_weight REAL NOT NULL,
                    temperature REAL NOT NULL,
                    word_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    output_filename TEXT,
                    duration_seconds REAL,
                    generation_seconds REAL,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_generations_created_at "
                "ON generations(created_at DESC)"
            )

    def recover_interrupted(self) -> None:
        """Önceki süreçte yarım kalan kayıtları anlaşılır biçimde işaretler."""
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE generations
                SET status = 'failed', stage = 'Uygulama yeniden başlatıldı.',
                    error = 'Üretim tamamlanmadan uygulama kapatıldı.', updated_at = ?
                WHERE status IN ('queued', 'processing')
                """,
                (now,),
            )

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        values = {
            **record,
            "status": "queued",
            "stage": "Sıraya alındı.",
            "output_filename": None,
            "duration_seconds": None,
            "generation_seconds": None,
            "is_favorite": 0,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO generations (
                    id, title, text, preset, exaggeration, cfg_weight,
                    temperature, word_count, status, stage, output_filename,
                    duration_seconds, generation_seconds, is_favorite, error,
                    created_at, updated_at
                ) VALUES (
                    :id, :title, :text, :preset, :exaggeration, :cfg_weight,
                    :temperature, :word_count, :status, :stage, :output_filename,
                    :duration_seconds, :generation_seconds, :is_favorite, :error,
                    :created_at, :updated_at
                )
                """,
                values,
            )
        return self.get(values["id"]) or values

    def get(self, generation_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM generations WHERE id = ?", (generation_id,)
            ).fetchone()
        return self._serialize(row)

    def list(
        self,
        *,
        search: str = "",
        favorite_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[Any] = []
        if search.strip():
            conditions.append("(title LIKE ? OR text LIKE ?)")
            pattern = f"%{search.strip()}%"
            parameters.extend([pattern, pattern])
        if favorite_only:
            conditions.append("is_favorite = 1")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parameters.extend([limit, offset])
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM generations
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                parameters,
            ).fetchall()
        return [self._serialize(row) for row in rows if row is not None]

    def update(self, generation_id: str, **fields: Any) -> dict[str, Any] | None:
        allowed = {
            "status",
            "stage",
            "output_filename",
            "duration_seconds",
            "generation_seconds",
            "is_favorite",
            "error",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return self.get(generation_id)
        updates["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE generations SET {assignments} WHERE id = ?",
                [*updates.values(), generation_id],
            )
        return self.get(generation_id)

    def delete(self, generation_id: str) -> dict[str, Any] | None:
        record = self.get(generation_id)
        if record is None:
            return None
        with self._connect() as connection:
            connection.execute("DELETE FROM generations WHERE id = ?", (generation_id,))
        return record

    def statistics(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(word_count), 0) AS total_words,
                    COALESCE(SUM(duration_seconds), 0) AS total_audio_seconds,
                    COALESCE(AVG(generation_seconds), 0) AS average_generation_seconds
                FROM generations
                WHERE status = 'completed'
                """
            ).fetchone()
        return dict(row) if row is not None else {}

