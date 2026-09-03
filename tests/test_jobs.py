"""GPU modeli yüklemeden üretim kuyruğunu sınayan testler."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

from backend.database import HistoryDatabase
from backend.jobs import GenerationQueue
from tts_service import TTSService


class FakeTTSService:
    """Gerçek model yerine kısa, sessiz bir ses dizisi döndürür."""

    def load_model(self, status_callback=None) -> None:
        if status_callback:
            status_callback("Sahte model hazır.")

    def synthesize_chunks(self, chunks, status_callback=None, **_settings):
        if status_callback:
            status_callback(f"Ses parçası 1/{len(chunks)} üretiliyor...")
        return np.zeros(2_400, dtype=np.float32)

    save_wav = staticmethod(TTSService.save_wav)


class GenerationQueueTests(unittest.TestCase):
    def test_queue_completes_and_saves_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = HistoryDatabase(root / "history.db")
            database.initialize()
            record = database.create(
                {
                    "id": "queue-test",
                    "title": "Kuyruk testi",
                    "text": "Merhaba Türkiye.",
                    "preset": "normal",
                    "exaggeration": 0.5,
                    "cfg_weight": 0.5,
                    "temperature": 0.8,
                    "word_count": 2,
                }
            )
            generation_queue = GenerationQueue(
                database,
                root / "outputs",
                service_factory=FakeTTSService,
            )

            generation_queue.start()
            generation_queue.enqueue(record["id"])
            deadline = time.monotonic() + 2
            updated = None
            while time.monotonic() < deadline:
                updated = database.get(record["id"])
                if updated and updated["status"] == "completed":
                    break
                time.sleep(0.01)
            generation_queue.stop()

            self.assertIsNotNone(updated)
            self.assertEqual(updated["status"], "completed")
            self.assertAlmostEqual(updated["duration_seconds"], 0.1)
            self.assertTrue((root / "outputs" / updated["output_filename"]).is_file())


if __name__ == "__main__":
    unittest.main()
