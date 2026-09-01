"""TTS servisinin model gerektirmeyen birim testleri."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

import numpy as np
import torch

from tts_service import SAMPLE_RATE, TTSService


class TTSServiceTests(unittest.TestCase):
    def test_synthesize_chunks_inserts_silence(self) -> None:
        service = TTSService()
        fake_model = Mock()
        status_messages: list[str] = []
        fake_model.generate.side_effect = [
            torch.tensor([[0.1, 0.2]], dtype=torch.float32),
            torch.tensor([[0.3, 0.4]], dtype=torch.float32),
        ]
        service._model = fake_model

        result = service.synthesize_chunks(
            ["Birinci.", "İkinci."],
            silence_ms=1,
            status_callback=status_messages.append,
        )

        self.assertEqual(fake_model.generate.call_count, 2)
        self.assertEqual(len(result), 2 + SAMPLE_RATE // 1_000 + 2)
        self.assertTrue(np.all(result[2 : 2 + SAMPLE_RATE // 1_000] == 0))
        self.assertIn("Ses parçası 1/2 üretiliyor...", status_messages)
        self.assertIn("Ses parçası 2/2 üretiliyor...", status_messages)

    def test_synthesize_chunks_rejects_empty_chunks(self) -> None:
        service = TTSService()

        with self.assertRaisesRegex(Exception, "en az bir"):
            service.synthesize_chunks([])


if __name__ == "__main__":
    unittest.main()
