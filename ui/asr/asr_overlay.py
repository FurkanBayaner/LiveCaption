"""Thin ASR overlay wrapper for the shared overlay window base."""

from __future__ import annotations

from ui.overlay_base import SharedOverlayWindow


class ASROverlay(SharedOverlayWindow):
    """ASR mode overlay window subclass with its own object name."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setObjectName("asrOverlay")
