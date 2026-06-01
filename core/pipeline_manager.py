"""Central controller for mutually exclusive OCR and ASR pipelines."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from core.app_state import AppState
from core.types import PipelineMode

LOGGER = logging.getLogger(__name__)


class Pipeline(Protocol):
    """Minimal lifecycle contract implemented by OCR and ASR pipelines."""

    def start(self) -> None:
        """Start background processing."""

    def stop(self) -> None:
        """Stop processing and release mode-specific resources."""


StateListener = Callable[[AppState], None]
ErrorListener = Callable[[str], None]


class PipelineManager:
    """Own start, stop and mode-lock decisions for live pipelines."""

    def __init__(
        self,
        *,
        state_listener: StateListener | None = None,
        error_listener: ErrorListener | None = None,
    ) -> None:
        self._state = AppState.IDLE
        self._active_mode: PipelineMode | None = None
        self._active_pipeline: Pipeline | None = None
        self._state_listener = state_listener
        self._error_listener = error_listener

    @property
    def state(self) -> AppState:
        """Return the current application state."""
        return self._state

    @property
    def active_mode(self) -> PipelineMode | None:
        """Return the active processing mode, if any."""
        return self._active_mode

    def start_ocr(self, pipeline: Pipeline) -> bool:
        """Start OCR if no live pipeline currently owns the mode lock."""
        return self._start(PipelineMode.OCR, pipeline)

    def start_asr(self, pipeline: Pipeline) -> bool:
        """Start ASR if no live pipeline currently owns the mode lock."""
        return self._start(PipelineMode.ASR, pipeline)

    def stop_active(self) -> bool:
        """Stop the active pipeline and always return to idle."""
        pipeline = self._active_pipeline
        if pipeline is None:
            return False

        try:
            pipeline.stop()
        except Exception as exc:  # Pipeline failures must not close the app.
            self._report_error("Failed to stop pipeline cleanly.", exc)
        finally:
            self._active_pipeline = None
            self._active_mode = None
            self._set_state(AppState.IDLE)

        return True

    def _start(self, mode: PipelineMode, pipeline: Pipeline) -> bool:
        if self._active_pipeline is not None:
            LOGGER.warning(
                "Rejected %s start request while %s is active.",
                mode.value,
                self._active_mode.value if self._active_mode else "unknown",
            )
            return False

        try:
            pipeline.start()
        except Exception as exc:  # Pipeline failures must not close the app.
            self._report_error(f"Failed to start {mode.value} pipeline.", exc)
            return False

        self._active_pipeline = pipeline
        self._active_mode = mode
        state = AppState.OCR_RUNNING if mode is PipelineMode.OCR else AppState.ASR_RUNNING
        self._set_state(state)
        return True

    def _set_state(self, state: AppState) -> None:
        self._state = state
        LOGGER.info("Application state changed to %s.", state.value)
        if self._state_listener is not None:
            self._state_listener(state)

    def _report_error(self, message: str, error: Exception) -> None:
        LOGGER.exception("%s", message, exc_info=error)
        if self._error_listener is not None:
            self._error_listener(message)
