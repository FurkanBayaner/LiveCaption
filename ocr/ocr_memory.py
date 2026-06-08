"""FIFO memory for OCR subtitle text."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable


class OCRMemory:
    """Store recent OCR texts and reject empty or repeated subtitles."""

    def __init__(self, max_items: int = 5) -> None:
        if max_items <= 0:
            raise ValueError("OCR memory max_items must be positive.")
        self._items: deque[str] = deque(maxlen=max_items)

    @property
    def items(self) -> tuple[str, ...]:
        """Return stored OCR history from oldest to newest."""
        return tuple(self._items)

    def add_if_new(self, text: str) -> bool:
        """Store text when it is non-empty and not already in recent memory."""
        normalized = self._normalize(text)
        if not normalized or normalized in self._items:
            return False

        self._items.append(normalized)
        return True

    def clear(self) -> None:
        """Remove all OCR history when the OCR pipeline stops."""
        self._items.clear()

    def extend(self, texts: Iterable[str]) -> None:
        """Add multiple texts using the same empty and duplicate rules."""
        for text in texts:
            self.add_if_new(text)

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.strip().split())
