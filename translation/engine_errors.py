"""Translation engine exception types."""

from __future__ import annotations


class TranslationEngineError(RuntimeError):
    """Raised when a translation engine cannot load or translate safely."""

