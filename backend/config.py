"""Arka uç yolları ve çalışma ayarları."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """FastAPI uygulamasının yerel çalışma ayarları."""

    database_path: Path = Path(
        os.environ.get("TTS_DATABASE_PATH", PROJECT_ROOT / "data" / "tts_history.db")
    )
    output_dir: Path = Path(
        os.environ.get("TTS_OUTPUT_DIR", PROJECT_ROOT / "outputs")
    )
    frontend_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )

