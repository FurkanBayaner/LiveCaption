"""Central registry for supported translation models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_MODELS_DIR = PROJECT_ROOT / "models" / "translation"
LLM_MODELS_DIR = TRANSLATION_MODELS_DIR / "llm"
MARIAN_MODELS_DIR = TRANSLATION_MODELS_DIR / "marian"


class TranslationEngineType(str, Enum):
    """Backend families supported by the translation subsystem."""

    LLM = "llm"
    MARIAN_MT = "marian_mt"


@dataclass(frozen=True, slots=True)
class TranslationModelSpec:
    """Metadata needed to select and load a translation model."""

    display_name: str
    engine_type: TranslationEngineType
    local_path: Path
    source_model_name: str | None = None


DEFAULT_TRANSLATION_ENGINE = "Qwen3 1.7B"

TRANSLATION_MODELS: tuple[TranslationModelSpec, ...] = (
    TranslationModelSpec(
        display_name="Qwen3 1.7B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "qwen3-1.7b",
    ),
    TranslationModelSpec(
        display_name="Qwen3.5 2B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "qwen3.5-2b",
    ),
    TranslationModelSpec(
        display_name="Gemma 2 2B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "gemma-2-2b",
    ),
    TranslationModelSpec(
        display_name="Qwen2.5 Coder 1.5B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "qwen2.5-coder-1.5b",
    ),
    TranslationModelSpec(
        display_name="Gemma 3 1B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "gemma-3-1b",
    ),
    TranslationModelSpec(
        display_name="Llama 3.2 1B",
        engine_type=TranslationEngineType.LLM,
        local_path=LLM_MODELS_DIR / "llama-3.2-1b",
    ),
    TranslationModelSpec(
        display_name="MarianMT",
        engine_type=TranslationEngineType.MARIAN_MT,
        local_path=MARIAN_MODELS_DIR / "opus-mt-en-tr",
        source_model_name="Helsinki-NLP/opus-mt-en-tr",
    ),
)

TRANSLATION_ENGINE_NAMES = tuple(model.display_name for model in TRANSLATION_MODELS)
TRANSLATION_MODEL_REGISTRY = {model.display_name: model for model in TRANSLATION_MODELS}


def _validate_registry() -> None:
    if len(TRANSLATION_MODEL_REGISTRY) != len(TRANSLATION_MODELS):
        raise ValueError("Translation model display names must be unique.")
    if DEFAULT_TRANSLATION_ENGINE not in TRANSLATION_MODEL_REGISTRY:
        raise ValueError("Default translation engine must be registered.")


_validate_registry()
DEFAULT_TRANSLATION_MODEL = TRANSLATION_MODEL_REGISTRY[DEFAULT_TRANSLATION_ENGINE]


def get_translation_model(display_name: str) -> TranslationModelSpec:
    """Return a registered translation model by its control-panel name."""
    try:
        return TRANSLATION_MODEL_REGISTRY[display_name]
    except KeyError as error:
        raise ValueError(f"Unsupported translation engine: {display_name}") from error
