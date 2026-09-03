"""Next.js arayüzüne hizmet veren FastAPI uygulaması."""

from __future__ import annotations

import platform
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import torch
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import Settings
from backend.database import HistoryDatabase
from backend.jobs import GenerationQueue
from backend.presets import PRESETS, TEMPLATES
from backend.schemas import FavoriteUpdate, GenerationCreate, GenerationEnvelope
from text_utils import TextValidationError, count_words, validate_text
from tts_service import get_tts_service


def _envelope(record: dict[str, Any]) -> dict[str, Any]:
    audio_url = (
        f"/api/generations/{record['id']}/audio"
        if record.get("output_filename")
        else None
    )
    return {"generation": record, "audio_url": audio_url}


def create_app(settings: Settings | None = None, *, start_worker: bool = True) -> FastAPI:
    app_settings = settings or Settings()
    database = HistoryDatabase(app_settings.database_path)
    generation_queue = GenerationQueue(database, app_settings.output_dir)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.initialize()
        database.recover_interrupted()
        app_settings.output_dir.mkdir(parents=True, exist_ok=True)
        if start_worker:
            generation_queue.start()
        yield
        generation_queue.stop()

    app = FastAPI(
        title="Türkçe TTS Studio API",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.frontend_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.database = database
    app.state.generation_queue = generation_queue
    app.state.settings = app_settings

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "Türkçe TTS Studio", "version": "2.0.0"}

    @app.get("/api/system")
    def system_info(request: Request) -> dict[str, Any]:
        cuda_available = torch.cuda.is_available()
        service = get_tts_service()
        return {
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cuda_available": cuda_available,
            "device": service.device,
            "device_name": torch.cuda.get_device_name(0) if cuda_available else "CPU",
            "model_loaded": service.is_model_loaded,
            "gpu_memory_allocated_mb": round(torch.cuda.memory_allocated(0) / 1024**2, 1)
            if cuda_available
            else 0,
            "gpu_memory_reserved_mb": round(torch.cuda.memory_reserved(0) / 1024**2, 1)
            if cuda_available
            else 0,
            "queue_size": request.app.state.generation_queue.pending_count,
            "statistics": request.app.state.database.statistics(),
        }

    @app.get("/api/presets")
    def presets() -> dict[str, Any]:
        return {"presets": PRESETS}

    @app.get("/api/templates")
    def templates() -> dict[str, Any]:
        return {"templates": TEMPLATES}

    @app.post(
        "/api/generations",
        response_model=GenerationEnvelope,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def create_generation(payload: GenerationCreate, request: Request) -> dict[str, Any]:
        try:
            cleaned_text = validate_text(payload.text)
        except TextValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        preset = PRESETS[payload.preset]
        title = (payload.title or cleaned_text[:60]).strip()
        if len(cleaned_text) > 60 and payload.title is None:
            title = f"{title.rstrip()}…"
        generation_id = uuid.uuid4().hex
        record = request.app.state.database.create(
            {
                "id": generation_id,
                "title": title or "İsimsiz konuşma",
                "text": cleaned_text,
                "preset": payload.preset,
                "exaggeration": payload.exaggeration
                if payload.exaggeration is not None
                else preset["exaggeration"],
                "cfg_weight": payload.cfg_weight
                if payload.cfg_weight is not None
                else preset["cfg_weight"],
                "temperature": payload.temperature
                if payload.temperature is not None
                else preset["temperature"],
                "word_count": count_words(cleaned_text),
            }
        )
        request.app.state.generation_queue.enqueue(generation_id)
        return _envelope(record)

    @app.get("/api/generations")
    def list_generations(
        request: Request,
        search: str = "",
        favorite: bool = False,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        records = request.app.state.database.list(
            search=search,
            favorite_only=favorite,
            limit=limit,
            offset=offset,
        )
        return {"generations": [_envelope(record) for record in records]}

    @app.get("/api/generations/{generation_id}", response_model=GenerationEnvelope)
    def get_generation(generation_id: str, request: Request) -> dict[str, Any]:
        record = request.app.state.database.get(generation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Konuşma kaydı bulunamadı.")
        return _envelope(record)

    @app.patch("/api/generations/{generation_id}/favorite", response_model=GenerationEnvelope)
    def update_favorite(
        generation_id: str,
        payload: FavoriteUpdate,
        request: Request,
    ) -> dict[str, Any]:
        record = request.app.state.database.update(
            generation_id, is_favorite=int(payload.is_favorite)
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Konuşma kaydı bulunamadı.")
        return _envelope(record)

    @app.get("/api/generations/{generation_id}/audio")
    def get_audio(generation_id: str, request: Request) -> FileResponse:
        record = request.app.state.database.get(generation_id)
        if record is None or not record.get("output_filename"):
            raise HTTPException(status_code=404, detail="Ses dosyası bulunamadı.")
        output_dir = Path(request.app.state.settings.output_dir).resolve()
        audio_path = (output_dir / record["output_filename"]).resolve()
        if audio_path.parent != output_dir or not audio_path.is_file():
            raise HTTPException(status_code=404, detail="Ses dosyası bulunamadı.")
        return FileResponse(audio_path, media_type="audio/wav", filename=audio_path.name)

    @app.delete("/api/generations/{generation_id}", status_code=204)
    def delete_generation(generation_id: str, request: Request) -> None:
        current = request.app.state.database.get(generation_id)
        if current is None:
            raise HTTPException(status_code=404, detail="Konuşma kaydı bulunamadı.")
        if current["status"] in {"queued", "processing"}:
            raise HTTPException(
                status_code=409,
                detail="Devam eden bir üretim silinemez.",
            )
        record = request.app.state.database.delete(generation_id)
        assert record is not None
        filename = record.get("output_filename")
        if filename:
            output_dir = Path(request.app.state.settings.output_dir).resolve()
            audio_path = (output_dir / filename).resolve()
            if audio_path.parent == output_dir and audio_path.is_file():
                audio_path.unlink()

    return app


app = create_app()
