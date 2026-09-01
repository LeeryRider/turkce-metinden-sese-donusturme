"""Chatterbox Multilingual V3 modelini yükleme ve ses üretme servisi."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parent
# Bu proje modeli kendi önbelleğinde tutar. Dışarıdan tanımlı bir HF_HOME,
# uygulamanın indirilmiş modeli bulamamasına neden olmamalı.
os.environ["HF_HOME"] = str(PROJECT_ROOT / ".cache" / "huggingface")

import numpy as np
import soundfile as sf
import torch

MODEL_VERSION = "v3"
LANGUAGE_ID = "tr"
SAMPLE_RATE = 24_000
DEFAULT_SILENCE_MS = 250
StatusCallback = Callable[[str], None]


class ModelLoadError(RuntimeError):
    """Chatterbox modeli kullanıcıya gösterilebilir bir nedenle yüklenemedi."""


class SynthesisError(RuntimeError):
    """Ses üretimi kullanıcıya gösterilebilir bir nedenle başarısız oldu."""


class TTSService:
    """Chatterbox V3 için tek örnekli, tembel yüklemeli Türkçe TTS servisi."""

    def __init__(self, status_callback: StatusCallback | None = None) -> None:
        self._model: Any | None = None
        self._model_lock = Lock()
        self._synthesis_lock = Lock()
        self._status_callback = status_callback
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _report_status(
        self,
        message: str,
        status_callback: StatusCallback | None = None,
    ) -> None:
        callback = status_callback or self._status_callback
        if callback is not None:
            callback(message)
        else:
            print(message)

    @staticmethod
    def _import_chatterbox() -> type[Any]:
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        except ImportError as error:
            print(f"Chatterbox içe aktarma hatası: {error!r}", file=sys.stderr)
            raise ModelLoadError(
                "Chatterbox bağımlılıkları yüklenemedi. "
                "Önce `pip install -r requirements-cuda.txt` komutunu çalıştırın."
            ) from error
        return ChatterboxMultilingualTTS

    def load_model(self, status_callback: StatusCallback | None = None) -> None:
        """Chatterbox V3 modelini yalnızca ilk çağrıda yükler."""
        if self._model is not None:
            return

        with self._model_lock:
            if self._model is not None:
                return

            self._report_status(
                f"Chatterbox V3 yükleniyor ({self.device})...",
                status_callback,
            )
            try:
                chatterbox = self._import_chatterbox()
                self._model = chatterbox.from_pretrained(
                    device=self.device,
                    t3_model=MODEL_VERSION,
                )
            except torch.cuda.OutOfMemoryError as error:
                torch.cuda.empty_cache()
                print(f"CUDA bellek hatası: {error!r}", file=sys.stderr)
                raise ModelLoadError("GPU belleği modeli yüklemek için yetersiz.") from error
            except ModelLoadError:
                raise
            except Exception as error:
                print(f"Model yükleme hatası: {error!r}", file=sys.stderr)
                raise ModelLoadError(
                    "Chatterbox modeli yüklenemedi. Model dosyalarını ve bağlantıyı kontrol edin."
                ) from error

            self._report_status("Chatterbox V3 hazır.", status_callback)

    def synthesize(
        self,
        text: str,
        status_callback: StatusCallback | None = None,
    ) -> np.ndarray:
        """Bir Türkçe metin parçasını tek kanallı ses dizisine dönüştürür."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise SynthesisError("Ses üretmek için metin girin.")

        self.load_model(status_callback)
        self._report_status("Türkçe ses üretiliyor...", status_callback)
        try:
            with self._synthesis_lock:
                waveform = self._model.generate(
                    cleaned_text,
                    language_id=LANGUAGE_ID,
                )
        except torch.cuda.OutOfMemoryError as error:
            torch.cuda.empty_cache()
            print(f"CUDA bellek hatası: {error!r}", file=sys.stderr)
            raise SynthesisError(
                "GPU belleği ses üretimi için yetersiz. Daha kısa bir metin deneyin."
            ) from error
        except Exception as error:
            print(f"Ses üretim hatası: {error!r}", file=sys.stderr)
            raise SynthesisError("Ses üretimi başarısız oldu. Lütfen tekrar deneyin.") from error

        self._report_status("Ses üretimi tamamlandı.", status_callback)
        return np.asarray(waveform.detach().cpu().numpy(), dtype=np.float32).reshape(-1)

    def synthesize_chunks(
        self,
        chunks: Sequence[str],
        silence_ms: int = DEFAULT_SILENCE_MS,
        status_callback: StatusCallback | None = None,
    ) -> np.ndarray:
        """Metin parçalarını sırayla üretir ve aralarına sessizlik ekler."""
        if not chunks:
            raise SynthesisError("Ses üretmek için en az bir metin parçası gerekir.")
        if silence_ms < 0:
            raise ValueError("Sessizlik süresi negatif olamaz.")

        silence = np.zeros(round(SAMPLE_RATE * silence_ms / 1_000), dtype=np.float32)
        audio_parts: list[np.ndarray] = []

        for index, chunk in enumerate(chunks, start=1):
            self._report_status(
                f"Ses parçası {index}/{len(chunks)} üretiliyor...",
                status_callback,
            )
            audio_parts.append(self.synthesize(chunk, status_callback))
            if index < len(chunks) and silence.size:
                audio_parts.append(silence)

        try:
            return np.concatenate(audio_parts)
        except MemoryError as error:
            print(f"Ses birleştirme bellek hatası: {error!r}", file=sys.stderr)
            raise SynthesisError("Ses parçaları birleştirilirken bellek yetersiz kaldı.") from error

    @staticmethod
    def save_wav(waveform: np.ndarray, output_path: Path) -> Path:
        """Ses dizisini 24 kHz mono WAV dosyası olarak kaydeder."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            sf.write(output_path, waveform, SAMPLE_RATE, subtype="PCM_16")
        except Exception as error:
            print(f"WAV kaydetme hatası: {error!r}", file=sys.stderr)
            raise SynthesisError("WAV dosyası kaydedilemedi.") from error
        return output_path


@lru_cache(maxsize=1)
def get_tts_service() -> TTSService:
    """Uygulamanın ömrü boyunca tek bir Chatterbox servisi döndürür."""
    return TTSService()
