"""Chatterbox Multilingual V3 ile Türkçe GPU kalite denemesi."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".cache" / "huggingface"))

import torch
import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from huggingface_hub import snapshot_download

OUTPUT_PATH = PROJECT_ROOT / "outputs" / "chatterbox_v3_test.wav"
TEST_TEXT = (
    "Merhaba. Bugün İstanbul'da hava oldukça güzel. "
    "Türkçe metinden sese dönüştürme uygulamasının yeni sesini dinliyorsunuz. "
    "Bu konuşma doğal, anlaşılır ve akıcı duyulmalıdır."
)
MODEL_FILES = [
    "ve.pt",
    "t3_mtl23ls_v3.safetensors",
    "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "conds.pt",
    "Cangjie5_TC.json",
]


def main() -> None:
    """V3 modelini GPU'da yükler ve sabit Türkçe örneği WAV olarak kaydeder."""
    if not torch.cuda.is_available():
        raise RuntimeError("Chatterbox testi için CUDA kullanılabilir değil.")

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print("Model dosyaları tek bağlantıyla kontrol ediliyor...")
    snapshot_download(
        repo_id="ResembleAI/chatterbox",
        revision="main",
        allow_patterns=MODEL_FILES,
        max_workers=1,
    )
    print("Chatterbox Multilingual V3 yükleniyor...")
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3")

    print("Türkçe ses üretiliyor...")
    waveform = model.generate(TEST_TEXT, language_id="tr")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(OUTPUT_PATH), waveform.cpu(), model.sr)
    print(f"Test başarılı: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
