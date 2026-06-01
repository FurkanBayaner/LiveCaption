"""Shared data structures used across LiveCaption modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PipelineMode(str, Enum):
    """Mutually exclusive live processing modes."""

    OCR = "ocr"
    ASR = "asr"


@dataclass(frozen=True, slots=True)
class ScreenRegion:
    """A rectangular screen region in logical pixels."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Screen region width and height must be positive.")


@dataclass(frozen=True, slots=True)
class OverlaySettings:
    """User-controlled overlay appearance settings."""

    font_family: str
    font_size_px: int
    letter_spacing_px: int
    line_spacing: float
    font_weight_active: bool
    speaker_color: str
    text_color: str
    background_opacity_percent: int

    def __post_init__(self) -> None:
        if not 0 <= self.background_opacity_percent <= 100:
            raise ValueError("Background opacity must be between 0 and 100.")
