"""CPU MarianMT translation engine."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from translation.backends import has_local_model_files
from translation.engine_errors import TranslationEngineError
from translation.model_registry import TranslationEngineType, TranslationModelSpec

LOGGER = logging.getLogger(__name__)


class MarianTranslationEngine:
    """Load, unload and run a local MarianMT model on CPU."""

    def __init__(self, model_spec: TranslationModelSpec, *, max_new_tokens: int = 256) -> None:
        if model_spec.engine_type is not TranslationEngineType.MARIAN_MT:
            raise ValueError("MarianTranslationEngine requires a MarianMT model spec.")

        self.model_spec = model_spec
        self.max_new_tokens = max_new_tokens
        self._tokenizer: Any | None = None
        self._model: Any | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether the MarianMT model is loaded."""
        return self._model is not None and self._tokenizer is not None

    def is_available(self) -> bool:
        """Return whether local MarianMT files exist."""
        return has_local_model_files(self.model_spec.local_path)

    def load(self) -> None:
        """Load the MarianMT model locally on CPU."""
        if self.is_loaded:
            return

        try:
            available = self.is_available()
        except OSError as error:
            message = f"Unable to inspect MarianMT model path: {self.model_spec.local_path}"
            self._log_exception("load", message)
            raise TranslationEngineError(message) from error

        if not available:
            message = f"MarianMT model path does not exist: {self.model_spec.local_path}"
            self._log_error("load", message)
            raise TranslationEngineError(message)

        try:
            from translation.llm_engine import LLMTranslationEngine

            LLMTranslationEngine.unload_active()
            from transformers import (  # type: ignore[import-not-found]
                AutoModelForSeq2SeqLM,
                AutoTokenizer,
            )

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_spec.local_path,
                local_files_only=True,
            )
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_spec.local_path,
                local_files_only=True,
            )
            self._model.to("cpu")
            self._log_info("load", "Loaded MarianMT translation engine.")
        except Exception as error:
            self._clear_loaded_objects()
            message = f"Unable to load MarianMT translation engine: {self.model_spec.display_name}"
            self._log_exception("load", message)
            raise TranslationEngineError(message) from error

    def unload(self) -> None:
        """Release the MarianMT model without touching CUDA state."""
        self._clear_loaded_objects()
        self._log_info("unload", "Unloaded MarianMT translation engine.")

    def translate(self, text: str, context: str | Sequence[str] | None = None) -> str:
        """Translate English text to Turkish using CPU MarianMT."""
        del context
        cleaned_text = text.strip()
        if not cleaned_text:
            return ""

        try:
            self.load()
            if self._tokenizer is None or self._model is None:
                raise TranslationEngineError("MarianMT model is not loaded.")

            inputs = self._tokenizer(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
            )
            outputs = self._model.generate(**inputs, max_new_tokens=self.max_new_tokens)
            decoded = self._tokenizer.batch_decode(outputs, skip_special_tokens=True)
            return decoded[0].strip() if decoded else ""
        except TranslationEngineError:
            raise
        except Exception as error:
            message = f"MarianMT translation failed: {self.model_spec.display_name}"
            self._log_exception("translate", message, text_len=len(cleaned_text))
            raise TranslationEngineError(message) from error

    def _clear_loaded_objects(self) -> None:
        self._model = None
        self._tokenizer = None

    def _log_info(self, phase: str, message: str, *, text_len: int | None = None) -> None:
        LOGGER.info(
            message,
            extra=self._log_extra(phase=phase, text_len=text_len),
        )

    def _log_error(self, phase: str, message: str, *, text_len: int | None = None) -> None:
        LOGGER.error(
            message,
            extra=self._log_extra(phase=phase, text_len=text_len),
        )

    def _log_exception(
        self, phase: str, message: str, *, text_len: int | None = None
    ) -> None:
        LOGGER.exception(
            message,
            extra=self._log_extra(phase=phase, text_len=text_len),
        )

    def _log_extra(self, *, phase: str, text_len: int | None = None) -> dict[str, object]:
        data: dict[str, object] = {
            "engine_name": self.model_spec.display_name,
            "engine_type": self.model_spec.engine_type.value,
            "phase": phase,
        }
        if text_len is not None:
            data["text_len"] = text_len
        return data
