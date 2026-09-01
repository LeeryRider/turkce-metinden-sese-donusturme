"""Gradio dönüşüm akışının model gerektirmeyen testleri."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

import app


class AppConversionTests(unittest.TestCase):
    def test_convert_text_streams_status_and_result(self) -> None:
        service = Mock()
        service.device = "cuda"
        service.load_model.side_effect = lambda status_callback: status_callback(
            "Chatterbox V3 hazır."
        )

        def synthesize(chunks, status_callback):
            status_callback(f"Ses parçası 1/{len(chunks)} üretiliyor...")
            return np.zeros(24, dtype=np.float32)

        service.synthesize_chunks.side_effect = synthesize
        service.save_wav.return_value = Path("outputs/test.wav")

        with patch.object(app, "get_tts_service", return_value=service):
            updates = list(app.convert_text("Merhaba Türkiye."))

        status_texts = [status for _, status in updates]
        self.assertIn("Metin kontrol ediliyor...", status_texts)
        self.assertIn("Chatterbox V3 hazır.", status_texts)
        self.assertIn("Ses parçası 1/1 üretiliyor...", status_texts)
        self.assertEqual(updates[-1][0], "outputs\\test.wav")
        self.assertIn("başarıyla", updates[-1][1])

    def test_convert_text_streams_validation_error(self) -> None:
        updates = list(app.convert_text("   "))

        self.assertEqual(updates[0], (None, "Metin kontrol ediliyor..."))
        self.assertEqual(updates[-1][0], None)
        self.assertIn("boş", updates[-1][1])


if __name__ == "__main__":
    unittest.main()
