"""Runtime OCR pipeline connecting capture, recognition, translation, and overlay."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import Protocol

from config import OCR_FPS
from core.types import ScreenRegion
from ocr.ocr_engine import OCREngineError, WindowsOCREngine
from ocr.ocr_memory import OCRMemory
from ocr.screen_capture import ScreenCapture, ScreenCaptureError
from translation.translation_router import TranslationRouter

LOGGER = logging.getLogger(__name__)

TextListener = Callable[[str], None]
ErrorListener = Callable[[str], None]
StopListener = Callable[[], None]
FinishListener = Callable[[], None]


class CaptureAdapter(Protocol):
    """Screen capture behavior used by the OCR pipeline."""

    def capture(self, region: ScreenRegion) -> object | None:
        """Return an OCR-ready frame for the region."""

    def close(self) -> None:
        """Release capture resources."""


class OCREngineAdapter(Protocol):
    """OCR engine behavior used by the OCR pipeline."""

    async def recognize_text(self, rgba_frame: object) -> str:
        """Return plain OCR text for an OCR-ready frame."""


class OCRPipeline:
    """Run OCR processing until stopped by the Pipeline Manager."""

    def __init__(
        self,
        *,
        subtitle_region: ScreenRegion,
        capture: CaptureAdapter | None = None,
        ocr_engine: OCREngineAdapter | None = None,
        translation_router: TranslationRouter,
        memory: OCRMemory | None = None,
        text_listener: TextListener | None = None,
        error_listener: ErrorListener | None = None,
        stop_listener: StopListener | None = None,
        finish_listener: FinishListener | None = None,
        fps: int = OCR_FPS,
    ) -> None:
        if fps <= 0:
            raise ValueError("OCR pipeline FPS must be positive.")

        self._subtitle_region = subtitle_region
        self._capture = capture or ScreenCapture()
        self._ocr_engine = ocr_engine or WindowsOCREngine()
        self._translation_router = translation_router
        self._memory = memory or OCRMemory()
        self._text_listener = text_listener
        self._error_listener = error_listener
        self._stop_listener = stop_listener
        self._finish_listener = finish_listener
        self._frame_interval_seconds = 1 / fps
        self._stop_event = threading.Event()
        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False
        self._thread: threading.Thread | None = None

    @property
    def memory(self) -> OCRMemory:
        """Return OCR memory, mainly for focused tests and diagnostics."""
        return self._memory

    @property
    def is_running(self) -> bool:
        """Return whether the worker thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start OCR processing in a background thread."""
        if self.is_running:
            return

        self._stop_event.clear()
        self._cleaned_up = False
        self._thread = threading.Thread(
            target=self._run_worker,
            name="LiveCaptionOCRPipeline",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop OCR processing, clear memory, and request overlay cleanup."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)

        self._cleanup()

    def _run_worker(self) -> None:
        try:
            while not self._stop_event.is_set():
                started_at = time.monotonic()
                try:
                    self._process_frame()
                except (OCREngineError, ScreenCaptureError) as exc:
                    self._report_error(str(exc))
                    self._stop_event.set()
                except Exception:
                    LOGGER.exception("Unexpected OCR pipeline error.")
                    self._report_error("Unexpected OCR pipeline error.")
                    self._stop_event.set()

                elapsed = time.monotonic() - started_at
                remaining = self._frame_interval_seconds - elapsed
                if remaining > 0:
                    self._stop_event.wait(remaining)
        finally:
            self._cleanup()
            if self._finish_listener is not None:
                self._finish_listener()

    def _process_frame(self) -> None:
        frame = self._capture.capture(self._subtitle_region)
        if frame is None:
            return

        text = asyncio.run(self._ocr_engine.recognize_text(frame))
        if not self._memory.add_if_new(text):
            return

        translated_text = self._translation_router.translate(text, self._memory.items)
        if not translated_text:
            return

        if self._text_listener is not None:
            self._text_listener(translated_text)

    def _cleanup(self) -> None:
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True

            try:
                self._capture.close()
            except Exception:
                LOGGER.exception("Failed to close OCR screen capture cleanly.")
            finally:
                self._memory.clear()
                if self._stop_listener is not None:
                    self._stop_listener()

    def _report_error(self, message: str) -> None:
        LOGGER.error("OCR pipeline error: %s", message)
        if self._error_listener is not None:
            self._error_listener(message)
