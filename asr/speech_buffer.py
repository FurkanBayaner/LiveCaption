"""Speech segment buffering after VAD classification."""

from __future__ import annotations

from dataclasses import dataclass

from config import ASR_MAX_WAIT_SECONDS, AUDIO_SAMPLE_RATE
from asr.audio_capture import AudioChunk


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    """A speech-only audio segment ready for ASR transcription."""

    samples: object
    sample_rate: int

    @property
    def duration_seconds(self) -> float:
        """Return segment duration in seconds."""
        return len(self.samples) / self.sample_rate


class SpeechSegmentBuffer:
    """Accumulate speech chunks and flush only speech segments."""

    def __init__(
        self,
        *,
        max_wait_seconds: float = ASR_MAX_WAIT_SECONDS,
        sample_rate: int = AUDIO_SAMPLE_RATE,
    ) -> None:
        if max_wait_seconds <= 0:
            raise ValueError("ASR max wait must be positive.")
        if sample_rate <= 0:
            raise ValueError("ASR sample rate must be positive.")

        self._max_wait_seconds = max_wait_seconds
        self._sample_rate = sample_rate
        self._chunks: list[object] = []
        self._duration_seconds = 0.0

    @property
    def is_empty(self) -> bool:
        """Return whether no speech is currently buffered."""
        return not self._chunks

    @property
    def duration_seconds(self) -> float:
        """Return currently buffered speech duration."""
        return self._duration_seconds

    def accept(self, chunk: AudioChunk, *, is_speech: bool) -> SpeechSegment | None:
        """Add speech chunks and flush when speech ends or max wait is reached."""
        if chunk.sample_rate != self._sample_rate:
            raise ValueError(
                f"Speech buffer expected {self._sample_rate} Hz audio, got {chunk.sample_rate} Hz."
            )

        if not is_speech:
            return self.flush()

        self._chunks.append(chunk.samples)
        self._duration_seconds += chunk.duration_seconds
        if self._duration_seconds >= self._max_wait_seconds:
            return self.flush()

        return None

    def flush(self) -> SpeechSegment | None:
        """Return the buffered speech segment and clear the buffer."""
        if not self._chunks:
            return None

        samples = concatenate_samples(self._chunks)
        self.clear()
        return SpeechSegment(samples=samples, sample_rate=self._sample_rate)

    def clear(self) -> None:
        """Drop any buffered speech."""
        self._chunks.clear()
        self._duration_seconds = 0.0


def concatenate_samples(chunks: list[object]) -> object:
    """Concatenate sample arrays without importing NumPy at module import time."""
    np = _import_numpy()
    return np.concatenate(chunks).astype(np.float32, copy=False)


def _import_numpy() -> object:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "NumPy is not installed. Install project requirements before ASR buffering."
        ) from exc
    return np
