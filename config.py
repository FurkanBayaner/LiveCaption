"""Central runtime defaults for LiveCaption."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
APP_LOG_PATH = LOGS_DIR / "app.log"

PYTHON_VERSION = "3.11.9"

OCR_FPS = 10
SCREEN_SCALE = 2.0

AUDIO_SAMPLE_RATE = 16_000
VAD_THRESHOLD = 0.5
ASR_MAX_WAIT_SECONDS = 10.0
WHISPER_MODEL_NAME = "medium"
WHISPER_MODEL_DIR = MODELS_DIR / "whisper"

TRANSLATION_MODELS_DIR = MODELS_DIR / "translation"
LLM_MODELS_DIR = TRANSLATION_MODELS_DIR / "llm"
MARIAN_MODELS_DIR = TRANSLATION_MODELS_DIR / "marian"
DEFAULT_TRANSLATION_ENGINE = "Qwen3 1.7B"
TRANSLATION_ENGINES = (
    "Qwen3 1.7B",
    "Qwen3.5 2B",
    "Gemma 2 2B",
    "Qwen2.5 Coder 1.5B",
    "Gemma 3 1B",
    "Llama 3.2 1B",
    "MarianMT",
)
MARIAN_MODEL_NAME = "Helsinki-NLP/opus-mt-en-tr"
LLM_LOAD_IN_8BIT = True

DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE_PX = 20
DEFAULT_LETTER_SPACING_PX = 0
DEFAULT_LINE_SPACING = 1.2
DEFAULT_FONT_WEIGHT_ACTIVE = False
DEFAULT_SPEAKER_COLOR = "Light Yellow"
DEFAULT_TEXT_COLOR = "White"
DEFAULT_BACKGROUND_OPACITY_PERCENT = 0

FONT_FAMILIES = (
    "Arial",
    "Tahoma",
    "Segoe UI",
    "Verdana",
    "Calibri",
    "Bahnschrift",
)
FONT_SIZES_PX = tuple(range(12, 41, 2))
LETTER_SPACING_OPTIONS_PX = tuple(range(-2, 11))
LINE_SPACING_OPTIONS = tuple(round(value / 10, 1) for value in range(10, 26))

COLOR_PALETTE = {
    "White": {"text": "#FFFFFF", "outline": "#000000"},
    "Light Yellow": {"text": "#BCA21F", "outline": "#000000"},
    "Light Gray": {"text": "#A0A0A0", "outline": "#000000"},
    "Black": {"text": "#000000", "outline": "#FFFFFF"},
    "Dark Gray": {"text": "#414141", "outline": "#FFFFFF"},
    "Blue": {"text": "#1450C7", "outline": "#FFFFFF"},
    "Green": {"text": "#079444", "outline": "#FFFFFF"},
    "Red": {"text": "#B32F2F", "outline": "#FFFFFF"},
}
