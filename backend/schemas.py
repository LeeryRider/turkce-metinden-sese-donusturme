"""FastAPI istek ve yanıt şemaları."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PresetName = Literal[
    "normal", "news", "announcement", "story", "education", "accessibility"
]


class GenerationCreate(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    title: str | None = Field(default=None, max_length=100)
    preset: PresetName = "normal"
    exaggeration: float | None = Field(default=None, ge=0.0, le=1.0)
    cfg_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    temperature: float | None = Field(default=None, ge=0.5, le=1.2)


class FavoriteUpdate(BaseModel):
    is_favorite: bool


class GenerationResponse(BaseModel):
    id: str
    title: str
    text: str
    preset: str
    exaggeration: float
    cfg_weight: float
    temperature: float
    word_count: int
    status: str
    stage: str
    output_filename: str | None
    duration_seconds: float | None
    generation_seconds: float | None
    is_favorite: bool
    error: str | None
    created_at: str
    updated_at: str

    @property
    def audio_url(self) -> str | None:
        if not self.output_filename:
            return None
        return f"/api/generations/{self.id}/audio"


class GenerationEnvelope(BaseModel):
    generation: GenerationResponse
    audio_url: str | None = None

