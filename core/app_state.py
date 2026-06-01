"""Central application states."""

from __future__ import annotations

from enum import Enum


class AppState(str, Enum):
    """Runtime state controlled by the Pipeline Manager."""

    IDLE = "idle"
    OCR_RUNNING = "ocr_running"
    ASR_RUNNING = "asr_running"
    LOADING_MODEL = "loading_model"
