"""ASR audio capture and VAD pipeline up to speech-segment output."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Protocol

from asr.audio_capture import AudioCaptureError, AudioChunk, WasapiLoopbackAudioCapture
from asr.speech_buffer import SpeechSegment, SpeechSegmentBuffer
from asr.vad_engine import SileroVADEngine, VADEngineError

LOGGER = logging.getLogger(__name__)

SegmentListener = Callable[[SpeechSegment], None]
ErrorListener = Callable[[str], None]
FinishListener = Callable[[], None]


class AudioCaptureAdapter(Protocol):
    """Audio capture behavior used by the ASR audio pipeline."""

    def start(self) -> None:
        """Open the audio capture stream."""

    def read_chunk(self) -> AudioChunk | None:
        """Read one audio chunk."""

    def close(self) -> None:
        """Release capture resources."""


class VADAdapter(Protocol):
    """Voice activity detector behavior used by the ASR audio pipeline."""

    def is_speech(self, chunk: AudioChunk) -> bool:
        """Return whether an audio chunk contains speech."""


class ASRAudioPipeline:
    """Turn system-output audio chunks into speech-only ASR segments."""

    def __init__(
        self,
        *,
        capture: AudioCaptureAdapter | None = None,
        vad_engine: VADAdapter | None = None,
        speech_buffer: SpeechSegmentBuffer | None = None,
        segment_listener: SegmentListener | None = None,
        error_listener: ErrorListener | None = None,
        finish_listener: FinishListener | None = None,
    ) -> None:
        self._capture = capture or WasapiLoopbackAudioCapture()
        self._vad_engine = vad_engine or SileroVADEngine()
        self._speech_buffer = speech_buffer or SpeechSegmentBuffer()
        self._segment_listener = segment_listener
        self._error_listener = error_listener
        self._finish_listener = finish_listener
        self._stop_event = threading.Event()
        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        """Return whether the audio worker thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start capture and VAD processing in a background thread."""
        if self.is_running:
            return

        self._stop_event.clear()
        self._cleaned_up = False
        self._thread = threading.Thread(
            target=self._run_worker,
            name="LiveCaptionASRAudioPipeline",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop capture, flush no extra audio, and clear buffered speech."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)

        self._cleanup()

    def _run_worker(self) -> None:
        try:
            self._capture.start()
            while not self._stop_event.is_set():
                chunk = self._capture.read_chunk()
                if chunk is None:
                    continue

                is_speech = self._vad_engine.is_speech(chunk)
                segment = self._speech_buffer.accept(chunk, is_speech=is_speech)
                if segment is not None and self._segment_listener is not None:
                    self._segment_listener(segment)
        except (AudioCaptureError, VADEngineError) as exc:
            self._report_error(str(exc))
            self._stop_event.set()
        except Exception:
            LOGGER.exception("Unexpected ASR audio pipeline error.")
            self._report_error("Unexpected ASR audio pipeline error.")
            self._stop_event.set()
        finally:
            self._cleanup()
            if self._finish_listener is not None:
                self._finish_listener()

    def _cleanup(self) -> None:
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True

            try:
                self._capture.close()
            except AudioCaptureError as exc:
                self._report_error(str(exc))
            finally:
                self._speech_buffer.clear()

    def _report_error(self, message: str) -> None:
        LOGGER.error("ASR audio pipeline error: %s", message)
        if self._error_listener is not None:
            self._error_listener(message)
