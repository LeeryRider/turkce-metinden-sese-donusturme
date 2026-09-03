"""FastAPI uçlarının model gerektirmeyen testleri."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        app = create_app(
            Settings(
                database_path=root / "history.db",
                output_dir=root / "outputs",
            ),
            start_worker=False,
        )
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_health_presets_and_templates(self) -> None:
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        self.assertIn("story", self.client.get("/api/presets").json()["presets"])
        self.assertGreater(len(self.client.get("/api/templates").json()["templates"]), 2)

    def test_generation_history_and_favorite(self) -> None:
        response = self.client.post(
            "/api/generations",
            json={"text": "Merhaba Türkiye.", "preset": "news"},
        )
        self.assertEqual(response.status_code, 202)
        generation = response.json()["generation"]
        self.assertEqual(generation["status"], "queued")
        self.assertEqual(generation["preset"], "news")

        generation_id = generation["id"]
        favorite = self.client.patch(
            f"/api/generations/{generation_id}/favorite",
            json={"is_favorite": True},
        )
        self.assertTrue(favorite.json()["generation"]["is_favorite"])

        history = self.client.get("/api/generations?favorite=true").json()
        self.assertEqual(len(history["generations"]), 1)

        blocked_delete = self.client.delete(f"/api/generations/{generation_id}")
        self.assertEqual(blocked_delete.status_code, 409)

        self.client.app.state.database.update(
            generation_id,
            status="failed",
            stage="Test için durduruldu.",
        )
        self.assertEqual(self.client.delete(f"/api/generations/{generation_id}").status_code, 204)

    def test_generation_rejects_empty_text(self) -> None:
        response = self.client.post("/api/generations", json={"text": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("boş", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
