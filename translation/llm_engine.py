"""LLM-backed translation engine with one-loaded-model VRAM discipline."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from threading import RLock
from typing import Any, ClassVar

from config import LLM_LOAD_IN_8BIT
from translation.backends import has_local_model_files
from translation.engine_errors import TranslationEngineError
from translation.model_registry import TranslationEngineType, TranslationModelSpec

LOGGER = logging.getLogger(__name__)


class LLMTranslationEngine:
    """Load, unload and run an INT8 local LLM translation model."""

    _lock: ClassVar[RLock] = RLock()
    _active_engine: ClassVar["LLMTranslationEngine | None"] = None

    def __init__(
        self,
        model_spec: TranslationModelSpec,
        *,
        max_new_tokens: int = 256,
    ) -> None:
        if model_spec.engine_type is not TranslationEngineType.LLM:
            raise ValueError("LLMTranslationEngine requires an LLM model spec.")

        self.model_spec = model_spec
        self.max_new_tokens = max_new_tokens
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._pipeline: Any | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether this engine currently owns a loaded LLM."""
        return self._pipeline is not None

    def is_available(self) -> bool:
        """Return whether local model files exist for this LLM."""
        return has_local_model_files(self.model_spec.local_path)

    @classmethod
    def unload_active(cls) -> None:
        """Unload the process-wide active LLM engine when one exists."""
        with cls._lock:
            if cls._active_engine is not None:
                cls._active_engine.unload()

    def load(self) -> None:
        """Load the LLM in INT8, unloading any other loaded LLM first."""
        with self._lock:
            if self.is_loaded:
                return

            active_engine = type(self)._active_engine
            if active_engine is not None and active_engine is not self:
                active_engine.unload()

            try:
                available = self.is_available()
            except OSError as error:
                message = f"Unable to inspect LLM model path: {self.model_spec.local_path}"
                self._log_exception("load", message)
                raise TranslationEngineError(message) from error

            if not available:
                message = f"LLM model path does not exist: {self.model_spec.local_path}"
                self._log_error("load", message)
                raise TranslationEngineError(message)

            try:
                from transformers import (  # type: ignore[import-not-found]
                    AutoModelForCausalLM,
                    AutoTokenizer,
                    BitsAndBytesConfig,
                    pipeline,
                )

                quantization_config = (
                    BitsAndBytesConfig(load_in_8bit=True) if LLM_LOAD_IN_8BIT else None
                )
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_spec.local_path,
                    local_files_only=True,
                )
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_spec.local_path,
                    device_map="auto",
                    local_files_only=True,
                    **(
                        {"quantization_config": quantization_config}
                        if quantization_config is not None
                        else {}
                    ),
                )
                self._pipeline = pipeline(
                    "text-generation",
                    model=self._model,
                    tokenizer=self._tokenizer,
                )
                type(self)._active_engine = self
                self._log_info("load", "Loaded LLM translation engine.")
            except Exception as error:
                self._clear_loaded_objects()
                message = f"Unable to load LLM translation engine: {self.model_spec.display_name}"
                self._log_exception("load", message)
                raise TranslationEngineError(message) from error

    def unload(self) -> None:
        """Release the loaded LLM and clear CUDA cache when available."""
        with self._lock:
            if not self.is_loaded and type(self)._active_engine is not self:
                return

            self._clear_loaded_objects()
            if type(self)._active_engine is self:
                type(self)._active_engine = None

            try:
                import torch  # type: ignore[import-not-found]
            except ModuleNotFoundError:
                torch = None

            if torch is not None:
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    self._log_exception(
                        "unload", "Unable to clear CUDA cache after LLM unload."
                    )

            self._log_info("unload", "Unloaded LLM translation engine.")

    def translate(self, text: str, context: str | Sequence[str] | None = None) -> str:
        """Translate English text to Turkish using the loaded LLM."""
        cleaned_text = text.strip()
        if not cleaned_text:
            return ""

        try:
            with self._lock:
                self.load()
                if self._pipeline is None:
                    raise TranslationEngineError("LLM pipeline is not loaded.")

                prompt = self.format_prompt(cleaned_text, context)
                outputs = self._pipeline(
                    prompt,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    return_full_text=False,
                )
                return self._extract_translation(outputs)
        except TranslationEngineError:
            raise
        except Exception as error:
            message = f"LLM translation failed: {self.model_spec.display_name}"
            self._log_exception("translate", message, text_len=len(cleaned_text))
            raise TranslationEngineError(message) from error

    @staticmethod
    def format_prompt(text: str, context: str | Sequence[str] | None = None) -> str:
        """Create the contextual translation prompt shared by local LLM models."""
        context_text = _context_to_text(context)
        context_block = f"\nContext:\n{context_text}\n" if context_text else ""
        return (
            "Translate the English subtitle text to natural Turkish.\n"
            "Preserve meaning, timing, names, and tone. Return only the Turkish translation.\n"
            f"{context_block}\nText:\n{text}\n\nTurkish:"
        )

    def _clear_loaded_objects(self) -> None:
        self._pipeline = None
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

    @staticmethod
    def _extract_translation(outputs: object) -> str:
        if isinstance(outputs, list) and outputs:
            first_output = outputs[0]
            if isinstance(first_output, dict):
                generated_text = first_output.get("generated_text", "")
                return str(generated_text).strip()
        return str(outputs).strip()


def _context_to_text(context: str | Sequence[str] | None) -> str:
    if context is None:
        return ""
    if isinstance(context, str):
        return context.strip()
    return "\n".join(item.strip() for item in context if item.strip())
