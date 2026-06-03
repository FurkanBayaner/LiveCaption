"""Prepare translation context without storing pipeline memory in the router."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranslationContext:
    """Source-agnostic context prepared from OCR or ASR history."""

    history: tuple[str, ...] = ()

    def as_prompt_context(self) -> str:
        """Return compact context text for contextual translation engines."""
        return "\n".join(self.history)


def prepare_translation_context(
    history: Iterable[str] | str | None,
    *,
    max_items: int = 5,
) -> TranslationContext:
    """Convert OCR or ASR history into bounded translation context."""
    if history is None:
        return TranslationContext()
    if isinstance(history, str):
        items = (history,)
    else:
        items = tuple(history)

    cleaned = tuple(item.strip() for item in items if item.strip())
    if max_items <= 0:
        return TranslationContext()
    return TranslationContext(history=cleaned[-max_items:])

