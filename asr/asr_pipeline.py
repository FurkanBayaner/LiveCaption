"""Full ASR pipeline connecting audio, Whisper, translation, and overlay output."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Protocol

from asr.asr_engine import ASREngineError, FasterWhisperASREngine
from asr.asr_memory import ASRMemory
from asr.audio_pipeline import ASRAudioPipeline
from asr.speech_buffer import SpeechSegment
from translation.translation_router import TranslationRouter

LOGGER = logging.getLogger(__name__)

TextListener = Callable[[str], None]
ErrorListener = Callable[[str], None]
StopListener = Callable[[], None]
FinishListener = Callable[[], None]


class SpeechSegmentSource(Protocol):
    """Lifecycle contract for a component that emits speech segments."""

    def start(self) -> None:
        """Start producing speech segments."""

    def stop(self) -> None:
        """Stop producing speech segments."""


class ASREngineAdapter(Protocol):
    """ASR engine behavior used by the ASR pipeline."""

    def transcribe_with_memory(
        self, segment: SpeechSegment, memory: ASRMemory
    ) -> object:
        """Transcribe a segment using ASR memory context."""

    def unload(self) -> None:
        """Release ASR model resources."""


class ASRPipeline:
    """Run ASR processing until stopped by the Pipeline Manager."""

    def __init__(
        self,
        *,
        audio_pipeline: SpeechSegmentSource | None = None,
        asr_engine: ASREngineAdapter | None = None,
        translation_router: TranslationRouter,
        memory: ASRMemory | None = None,
        text_listener: TextListener | None = None,
        error_listener: ErrorListener | None = None,
        stop_listener: StopListener | None = None,
        finish_listener: FinishListener | None = None,
    ) -> None:
        self._memory = memory or ASRMemory()
        self._asr_engine = asr_engine or FasterWhisperASREngine()
        self._translation_router = translation_router
        self._text_listener = text_listener
        self._error_listener = error_listener
        self._stop_listener = stop_listener
        self._finish_listener = finish_listener
        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False
        self._audio_pipeline = audio_pipeline or ASRAudioPipeline(
            segment_listener=self._process_segment,
            error_listener=self._report_error,
            finish_listener=self._finish,
        )

    @property
    def memory(self) -> ASRMemory:
        """Return ASR transcript memory for diagnostics and focused tests."""
        return self._memory

    def start(self) -> None:
        """Start the ASR audio/transcription pipeline."""
        self._cleaned_up = False
        self._audio_pipeline.start()

    def stop(self) -> None:
        """Stop ASR and clear memory/overlay state."""
        self._audio_pipeline.stop()
        self._cleanup()

    def _process_segment(self, segment: SpeechSegment) -> None:
        try:
            transcript = self._asr_engine.transcribe_with_memory(segment, self._memory)
        except ASREngineError as exc:
            self._report_error(str(exc))
            self.stop()
            return
        except Exception:
            LOGGER.exception("Unexpected ASR transcription error.")
            self._report_error("Unexpected ASR transcription error.")
            self.stop()
            return

        text = getattr(transcript, "text", "").strip()
        if not text:
            return
        if not self._memory.add_if_new(text):
            return

        translated_text = self._translation_router.translate(text, self._memory.items)
        if not translated_text:
            return

        if self._text_listener is not None:
            self._text_listener(translated_text)

    def _finish(self) -> None:
        self._cleanup()
        if self._finish_listener is not None:
            self._finish_listener()

    def _cleanup(self) -> None:
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True

            try:
                self._asr_engine.unload()
            except Exception:
                LOGGER.exception("Failed to unload ASR engine cleanly.")
            finally:
                self._memory.clear()
                if self._stop_listener is not None:
                    self._stop_listener()

    def _report_error(self, message: str) -> None:
        LOGGER.error("ASR pipeline error: %s", message)
        if self._error_listener is not None:
            self._error_listener(message)
