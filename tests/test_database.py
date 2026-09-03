"""SQLite konuşma geçmişi testleri."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.database import HistoryDatabase


class HistoryDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = HistoryDatabase(Path(self.temp_dir.name) / "history.db")
        self.database.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_record(self, generation_id: str = "record-1") -> dict:
        return self.database.create(
            {
                "id": generation_id,
                "title": "Deneme kaydı",
                "text": "Merhaba Türkiye.",
                "preset": "normal",
                "exaggeration": 0.5,
                "cfg_weight": 0.5,
                "temperature": 0.8,
                "word_count": 2,
            }
        )

    def test_create_search_favorite_and_delete(self) -> None:
        record = self.create_record()
        self.assertEqual(record["status"], "queued")

        results = self.database.list(search="Deneme")
        self.assertEqual([item["id"] for item in results], ["record-1"])

        favorite = self.database.update("record-1", is_favorite=1)
        self.assertTrue(favorite["is_favorite"])
        self.assertEqual(len(self.database.list(favorite_only=True)), 1)

        deleted = self.database.delete("record-1")
        self.assertEqual(deleted["id"], "record-1")
        self.assertIsNone(self.database.get("record-1"))

    def test_recover_interrupted_marks_record_failed(self) -> None:
        self.create_record()
        self.database.update("record-1", status="processing", stage="Üretiliyor")

        self.database.recover_interrupted()

        record = self.database.get("record-1")
        self.assertEqual(record["status"], "failed")
        self.assertIn("kapatıldı", record["error"])


if __name__ == "__main__":
    unittest.main()

