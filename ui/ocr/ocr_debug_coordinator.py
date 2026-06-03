"""Coordinate the opt-in OCR subtitle capture preview."""

from __future__ import annotations

from PyQt5.QtCore import QObject

from core.signals import ApplicationSignals
from core.types import ScreenRegion
from ui.ocr.ocr_debug_preview import OCRDebugPreview


class OCRDebugCoordinator(QObject):
    """Open a 30 FPS preview only when the user explicitly requests it."""

    def __init__(self, signals: ApplicationSignals) -> None:
        super().__init__()
        self.preview = OCRDebugPreview()
        self._subtitle_region: ScreenRegion | None = None

        signals.start_ocr_requested.connect(self._remember_ocr_region)
        signals.ocr_debug_preview_requested.connect(self.open_preview)
        signals.stop_requested.connect(self.preview.hide)

    def open_preview(self) -> None:
        """Show the last confirmed OCR subtitle region when one exists."""
        if self._subtitle_region is None:
            return
        self.preview.set_region(self._subtitle_region)
        self.preview.show()
        self.preview.place_away_from_source()
        self.preview.raise_()

    def _remember_ocr_region(
        self, subtitle_region: ScreenRegion, translation_region: ScreenRegion
    ) -> None:
        del translation_region
        self._subtitle_region = subtitle_region
        if self.preview.isVisible():
            self.preview.set_region(subtitle_region)
            self.preview.place_away_from_source()
