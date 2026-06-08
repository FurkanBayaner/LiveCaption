"""faster-whisper adapter for English ASR transcription."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import WHISPER_MODEL_DIR, WHISPER_MODEL_NAME
from asr.asr_memory import ASRMemory
from asr.speech_buffer import SpeechSegment


class ASREngineError(RuntimeError):
    """Raised when faster-whisper cannot load or transcribe."""


@dataclass(frozen=True, slots=True)
class ASRTranscript:
    """Plain transcript returned by the ASR engine."""

    text: str

    @property
    def is_empty(self) -> bool:
        """Return whether this transcript should be ignored by the pipeline."""
        return self.text == ""


def normalize_transcript(parts: list[str]) -> str:
    """Normalize faster-whisper segment text into one transcript string."""
    return " ".join(part.strip() for part in parts if part.strip()).strip()


class FasterWhisperASREngine:
    """Transcribe speech segments with faster-whisper/CTranslate2."""

    def __init__(
        self,
        *,
        model_name: str = WHISPER_MODEL_NAME,
        model_dir: object = WHISPER_MODEL_DIR,
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "en",
        model: Any | None = None,
    ) -> None:
        self._model_name = model_name
        self._model_dir = model_dir
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model = model

    @property
    def model_name(self) -> str:
        """Return the configured faster-whisper model name."""
        return self._model_name

    @property
    def language(self) -> str:
        """Return the transcription language."""
        return self._language

    def transcribe(
        self,
        segment: SpeechSegment,
        *,
        initial_prompt: str = "",
    ) -> ASRTranscript:
        """Transcribe a speech segment and return normalized text."""
        if len(segment.samples) == 0:
            return ASRTranscript("")

        model = self._get_model()
        try:
            segments, _info = model.transcribe(
                segment.samples,
                language=self._language,
                initial_prompt=initial_prompt or None,
                vad_filter=False,
            )
            parts = [item.text for item in segments]
        except Exception as exc:
            raise ASREngineError("faster-whisper failed to transcribe speech.") from exc

        return ASRTranscript(normalize_transcript(parts))

    def transcribe_with_memory(
        self, segment: SpeechSegment, memory: ASRMemory
    ) -> ASRTranscript:
        """Transcribe using ASR memory as the Whisper initial_prompt source."""
        return self.transcribe(segment, initial_prompt=memory.initial_prompt())

    def unload(self) -> None:
        """Release the local model reference."""
        self._model = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASREngineError(
                "faster-whisper is not installed. Install project requirements before ASR."
            ) from exc

        try:
            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
                download_root=str(self._model_dir),
            )
        except Exception as exc:
            raise ASREngineError("Failed to load faster-whisper ASR model.") from exc

        return self._model
