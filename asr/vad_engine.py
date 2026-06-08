"""Silero VAD adapter for ASR speech gating."""

from __future__ import annotations

from typing import Any

from config import AUDIO_SAMPLE_RATE, VAD_THRESHOLD
from asr.audio_capture import AudioChunk


class VADEngineError(RuntimeError):
    """Raised when voice activity detection cannot run."""


class SileroVADEngine:
    """Classify audio chunks as speech or non-speech using Silero VAD."""

    def __init__(
        self,
        *,
        threshold: float = VAD_THRESHOLD,
        sample_rate: int = AUDIO_SAMPLE_RATE,
        model: Any | None = None,
    ) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("VAD threshold must be between 0 and 1.")
        if sample_rate <= 0:
            raise ValueError("VAD sample rate must be positive.")

        self._threshold = threshold
        self._sample_rate = sample_rate
        self._model = model
        self._uses_injected_model = model is not None

    @property
    def threshold(self) -> float:
        """Return the speech probability threshold."""
        return self._threshold

    def is_speech(self, chunk: AudioChunk) -> bool:
        """Return whether a chunk contains speech."""
        if chunk.sample_rate != self._sample_rate:
            raise VADEngineError(
                f"VAD expected {self._sample_rate} Hz audio, got {chunk.sample_rate} Hz."
            )
        if len(chunk.samples) == 0:
            return False

        probability = self.speech_probability(chunk)
        return probability >= self._threshold

    def speech_probability(self, chunk: AudioChunk) -> float:
        """Return Silero's speech probability for a chunk."""
        model = self._get_model()
        try:
            if self._uses_injected_model:
                audio_tensor = chunk.samples
            else:
                torch = _import_torch()
                audio_tensor = torch.as_tensor(chunk.samples, dtype=torch.float32)
            probability = model(audio_tensor, chunk.sample_rate).item()
        except Exception as exc:
            raise VADEngineError("Silero VAD failed to classify the audio chunk.") from exc

        return float(probability)

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            from silero_vad import load_silero_vad
        except ImportError as exc:
            raise VADEngineError(
                "silero-vad is not installed. Install project requirements before ASR VAD."
            ) from exc

        try:
            self._model = load_silero_vad()
        except Exception as exc:
            raise VADEngineError("Failed to load Silero VAD model.") from exc

        return self._model


def _import_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise VADEngineError(
            "torch is not installed. Install the CUDA-compatible torch build before ASR VAD."
        ) from exc
    return torch
