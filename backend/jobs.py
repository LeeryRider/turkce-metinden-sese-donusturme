"""Chatterbox üretimlerini tek GPU işçisiyle sıraya alan servis."""

from __future__ import annotations

import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from backend.database import HistoryDatabase
from tts_service import (
    ModelLoadError,
    SAMPLE_RATE,
    SynthesisError,
    TTSService,
    get_tts_service,
)


class GenerationQueue:
    """GPU belleğini korumak için işleri sırayla çalıştıran kuyruk."""

    def __init__(
        self,
        database: HistoryDatabase,
        output_dir: Path,
        service_factory: Callable[[], TTSService] = get_tts_service,
    ) -> None:
        self.database = database
        self.output_dir = output_dir
        self.service_factory = service_factory
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._thread: threading.Thread | None = None

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run,
            name="tts-generation-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        self._queue.put(None)
        self._thread.join(timeout=2)

    def enqueue(self, generation_id: str) -> None:
        self._queue.put(generation_id)

    def _run(self) -> None:
        while True:
            generation_id = self._queue.get()
            try:
                if generation_id is None:
                    return
                self._process(generation_id)
            finally:
                self._queue.task_done()

    def _process(self, generation_id: str) -> None:
        record = self.database.get(generation_id)
        if record is None:
            return

        started_at = time.perf_counter()

        def report(message: str) -> None:
            self.database.update(generation_id, status="processing", stage=message)

        try:
            report("Metin hazırlanıyor...")
            from text_utils import split_text_into_chunks

            chunks = split_text_into_chunks(record["text"])
            report(f"Metin {len(chunks)} parçaya ayrıldı.")
            service = self.service_factory()
            service.load_model(status_callback=report)
            waveform = service.synthesize_chunks(
                chunks,
                status_callback=report,
                exaggeration=record["exaggeration"],
                cfg_weight=record["cfg_weight"],
                temperature=record["temperature"],
            )
            report("WAV dosyası kaydediliyor...")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"tts_{timestamp}_{generation_id[:8]}.wav"
            saved_path = service.save_wav(waveform, self.output_dir / filename)
            elapsed = time.perf_counter() - started_at
            duration = len(waveform) / SAMPLE_RATE
            self.database.update(
                generation_id,
                status="completed",
                stage="Ses başarıyla oluşturuldu.",
                output_filename=saved_path.name,
                duration_seconds=round(duration, 3),
                generation_seconds=round(elapsed, 3),
                error=None,
            )
        except (ModelLoadError, SynthesisError, ValueError) as error:
            self.database.update(
                generation_id,
                status="failed",
                stage="Üretim başarısız oldu.",
                error=str(error),
                generation_seconds=round(time.perf_counter() - started_at, 3),
            )
        except Exception as error:  # Beklenmeyen ayrıntı yalnızca yerel kayda yazılır.
            print(f"Beklenmeyen kuyruk hatası: {error!r}")
            self.database.update(
                generation_id,
                status="failed",
                stage="Beklenmeyen bir hata oluştu.",
                error="Beklenmeyen bir üretim hatası oluştu.",
                generation_seconds=round(time.perf_counter() - started_at, 3),
            )

