"""FIFO memory for ASR transcripts and Whisper context prompts."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable


class ASRMemory:
    """Store recent transcripts separately from OCR memory."""

    def __init__(self, max_items: int = 5) -> None:
        if max_items <= 0:
            raise ValueError("ASR memory max_items must be positive.")
        self._items: deque[str] = deque(maxlen=max_items)

    @property
    def items(self) -> tuple[str, ...]:
        """Return stored transcript history from oldest to newest."""
        return tuple(self._items)

    def add_if_new(self, transcript: str) -> bool:
        """Store transcript when it is non-empty and not already recent."""
        normalized = self._normalize(transcript)
        if not normalized or normalized in self._items:
            return False

        self._items.append(normalized)
        return True

    def initial_prompt(self, *, max_items: int = 5) -> str:
        """Return recent ASR history formatted for faster-whisper initial_prompt."""
        if max_items <= 0:
            return ""
        return " ".join(self.items[-max_items:])

    def clear(self) -> None:
        """Clear ASR history when the ASR pipeline stops."""
        self._items.clear()

    def extend(self, transcripts: Iterable[str]) -> None:
        """Add multiple transcripts using the same empty and duplicate rules."""
        for transcript in transcripts:
            self.add_if_new(transcript)

    @staticmethod
    def _normalize(transcript: str) -> str:
        return " ".join(transcript.strip().split())
