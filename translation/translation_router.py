"""Source-agnostic routing for translation backends."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from threading import RLock

from translation.backends import TranslationBackend
from translation.engine_errors import TranslationEngineError
from translation.llm_engine import LLMTranslationEngine
from translation.marian_engine import MarianTranslationEngine
from translation.model_registry import (
    DEFAULT_TRANSLATION_ENGINE,
    TranslationEngineType,
    TranslationModelSpec,
    get_translation_model,
)
from translation.translation_memory import prepare_translation_context

LOGGER = logging.getLogger(__name__)
ErrorListener = Callable[[str], None]
BackendFactory = Callable[[TranslationModelSpec], TranslationBackend]


class TranslationRouter:
    """Select the active engine and route OCR/ASR text without source knowledge."""

    def __init__(
        self,
        default_engine: str = DEFAULT_TRANSLATION_ENGINE,
        *,
        error_listener: ErrorListener | None = None,
        backend_factory: BackendFactory | None = None,
    ) -> None:
        self._lock = RLock()
        self._error_listener = error_listener
        self._backend_factory = backend_factory or self._create_backend
        self._active_spec = get_translation_model(default_engine)
        self._active_backend: TranslationBackend | None = None

    @property
    def active_engine_name(self) -> str:
        """Return the currently selected control-panel engine name."""
        return self._active_spec.display_name

    @property
    def active_backend(self) -> TranslationBackend | None:
        """Return the loaded or prepared backend instance, when one exists."""
        return self._active_backend

    def switch_engine(self, display_name: str) -> bool:
        """Switch engines without requiring OCR or ASR pipeline restart."""
        with self._lock:
            next_spec = get_translation_model(display_name)
            if next_spec.display_name == self._active_spec.display_name:
                return False

            previous_spec = self._active_spec
            previous_backend = self._active_backend
            next_backend = self._backend_factory(next_spec)
            if not self._backend_is_available(next_backend):
                return False

            self._unload_active_backend()
            self._active_spec = next_spec
            try:
                next_backend.load()
            except TranslationEngineError as error:
                self._active_spec = previous_spec
                self._restore_previous_backend(previous_backend)
                self._report_engine_error(error)
                return False

            self._active_backend = next_backend
            LOGGER.info("Switched translation engine: %s", next_spec.display_name)
            return True

    def translate(self, text: str, context: Iterable[str] | str | None = None) -> str:
        """Translate text with the selected backend, regardless of OCR or ASR source."""
        cleaned_text = text.strip()
        if not cleaned_text:
            return ""

        prepared_context = prepare_translation_context(context).as_prompt_context()
        with self._lock:
            backend = self._ensure_active_backend()
            try:
                return backend.translate(cleaned_text, prepared_context)
            except TranslationEngineError as error:
                self._report_engine_error(error)
                return ""

    def unload(self) -> None:
        """Unload the current backend while keeping the selected engine name."""
        with self._lock:
            self._unload_active_backend()

    def _ensure_active_backend(self) -> TranslationBackend:
        if self._active_backend is None:
            self._active_backend = self._backend_factory(self._active_spec)
        return self._active_backend

    def _unload_active_backend(self) -> None:
        if self._active_backend is None:
            return
        try:
            self._active_backend.unload()
        except TranslationEngineError as error:
            self._report_engine_error(error)
        finally:
            self._active_backend = None

    def _restore_previous_backend(self, backend: TranslationBackend | None) -> None:
        if backend is None:
            return
        try:
            backend.load()
        except TranslationEngineError as error:
            self._active_backend = None
            self._report_engine_error(error)
            return
        self._active_backend = backend

    def _backend_is_available(self, backend: TranslationBackend) -> bool:
        try:
            if backend.is_available():
                return True
        except OSError as error:
            message = f"Unable to inspect translation model path: {backend.model_spec.local_path}"
            self._report_engine_error(TranslationEngineError(message))
            LOGGER.exception(message)
            return False

        message = f"Translation model path does not exist: {backend.model_spec.local_path}"
        self._report_engine_error(TranslationEngineError(message))
        return False

    def _report_engine_error(self, error: TranslationEngineError) -> None:
        message = str(error)
        LOGGER.error("Translation engine error: %s", message)
        if self._error_listener is not None:
            self._error_listener(message)

    @staticmethod
    def _create_backend(model_spec: TranslationModelSpec) -> TranslationBackend:
        if model_spec.engine_type is TranslationEngineType.LLM:
            return LLMTranslationEngine(model_spec)
        if model_spec.engine_type is TranslationEngineType.MARIAN_MT:
            return MarianTranslationEngine(model_spec)
        raise ValueError(f"Unsupported translation engine type: {model_spec.engine_type}")
