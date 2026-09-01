"""Türkçe metni Chatterbox Multilingual V3 ile sese dönüştüren Gradio uygulaması."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(PROJECT_ROOT / ".cache" / "huggingface")

import gradio as gr

from text_utils import (
    MAX_WORDS,
    TextValidationError,
    count_words,
    split_text_into_chunks,
    validate_text,
)
from tts_service import ModelLoadError, SynthesisError, get_tts_service

OUTPUT_DIR = PROJECT_ROOT / "outputs"
ConversionOutput = tuple[str | None, str]
ConversionEvent = tuple[str, str | ConversionOutput]


def word_count_label(text: str) -> str:
    """Arayüzde gösterilecek kelime sayacı metnini üretir."""
    return f"{count_words(text)} / {MAX_WORDS} kelime"


def output_path() -> Path:
    """Tarih ve saat içeren benzersiz WAV çıktı yolunu oluşturur."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return OUTPUT_DIR / f"tts_{timestamp}.wav"


def _conversion_worker(text: str, events: Queue[ConversionEvent]) -> None:
    """Dönüştürmeyi arka planda yapar ve durum olaylarını kuyruğa gönderir."""
    report_status = lambda message: events.put(("status", message))

    try:
        report_status("Metin kontrol ediliyor...")
        cleaned_text = validate_text(text)
        chunks = split_text_into_chunks(cleaned_text)
        report_status(f"Metin {len(chunks)} ses parçasına ayrıldı.")

        tts_service = get_tts_service()
        tts_service.load_model(status_callback=report_status)
        waveform = tts_service.synthesize_chunks(
            chunks,
            status_callback=report_status,
        )

        report_status("WAV dosyası kaydediliyor...")
        saved_path = tts_service.save_wav(waveform, output_path())
    except (TextValidationError, ModelLoadError, SynthesisError) as error:
        events.put(("done", (None, str(error))))
    except Exception as error:
        print(f"Beklenmeyen dönüştürme hatası: {error!r}", file=sys.stderr)
        events.put(
            (
                "done",
                (None, "Beklenmeyen bir hata oluştu. Ayrıntılar terminale yazıldı."),
            )
        )
    else:
        events.put(
            (
                "done",
                (
                    str(saved_path),
                    f"Ses başarıyla oluşturuldu ({len(chunks)} parça). "
                    "Oynatabilir veya indirebilirsiniz.",
                ),
            )
        )


def convert_text(text: str) -> Iterator[ConversionOutput]:
    """Dönüştürme sırasında ses çıktısı ve canlı durum güncellemeleri üretir."""
    events: Queue[ConversionEvent] = Queue()
    worker = Thread(target=_conversion_worker, args=(text, events), daemon=True)
    worker.start()

    while True:
        event_type, payload = events.get()
        if event_type == "status":
            yield None, str(payload)
            continue

        if not isinstance(payload, tuple):
            raise RuntimeError("Geçersiz dönüştürme sonucu alındı.")
        yield payload
        return


def clear_form() -> tuple[str, str, None, str]:
    """Arayüz alanlarını başlangıç durumuna döndürür."""
    return "", word_count_label(""), None, ""


with gr.Blocks(title="Türkçe Metinden Sese Dönüştürme") as demo:
    gr.Markdown("# Türkçe Metinden Sese Dönüştürme")
    gr.Markdown("Chatterbox Multilingual V3 ile doğal Türkçe WAV sesi oluşturun.")

    text_input = gr.Textbox(
        label="Türkçe metin",
        placeholder="Seslendirmek istediğiniz metni yazın...",
        lines=10,
    )
    word_count = gr.Textbox(
        label="Kelime sayısı",
        value=word_count_label(""),
        interactive=False,
    )

    with gr.Row():
        convert_button = gr.Button("Sese Dönüştür", variant="primary")
        clear_button = gr.Button("Temizle")

    status = gr.Textbox(label="Durum", interactive=False)
    audio_output = gr.Audio(label="Oluşturulan ses", type="filepath", format="wav")

    text_input.input(
        word_count_label,
        inputs=text_input,
        outputs=word_count,
        queue=False,
    )
    convert_button.click(convert_text, inputs=text_input, outputs=[audio_output, status])
    clear_button.click(
        clear_form,
        outputs=[text_input, word_count, audio_output, status],
    )

demo.queue(default_concurrency_limit=1)


if __name__ == "__main__":
    demo.launch()
