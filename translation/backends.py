"""Shared translation backend protocol."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from translation.model_registry import TranslationModelSpec


class TranslationBackend(Protocol):
    """Common contract implemented by translation engines."""

    model_spec: TranslationModelSpec

    @property
    def is_loaded(self) -> bool:
        """Return whether the backend has a model in memory."""

    def is_available(self) -> bool:
        """Return whether required local model files exist."""

    def load(self) -> None:
        """Load the backend model."""

    def unload(self) -> None:
        """Release the backend model."""

    def translate(self, text: str, context: str | Sequence[str] | None = None) -> str:
        """Translate text using the backend."""


def has_local_model_files(path: Path) -> bool:
    """Return whether a local model directory exists and contains files."""
    return path.exists() and path.is_dir() and any(path.iterdir())
