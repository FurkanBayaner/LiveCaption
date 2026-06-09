"""Application-owned shared overlay instances and live appearance updates."""

from __future__ import annotations

from PyQt5.QtCore import QObject

from core.signals import ApplicationSignals
from core.types import OverlaySettings, ScreenRegion
from ui.asr.asr_overlay import ASROverlay
from ui.ocr.ocr_overlay import OCROverlay
from ui.overlay_base import SharedOverlayWindow


class OverlayCoordinator(QObject):
    """Keep OCR and ASR overlays alive and apply settings without pipeline restarts."""

    def __init__(self, signals: ApplicationSignals, settings: OverlaySettings) -> None:
        super().__init__()
        self.ocr_overlay = OCROverlay(settings)
        self.asr_overlay = ASROverlay(settings)

        signals.overlay_settings_changed.connect(self.apply_settings)
        signals.ocr_translation_ready.connect(self.update_ocr_text)
        signals.ocr_overlay_clear_requested.connect(self.hide_ocr)
        signals.asr_translation_ready.connect(self.update_asr_text)
        signals.asr_overlay_clear_requested.connect(self.hide_asr)
        signals.start_ocr_requested.connect(self._show_ocr_from_selection)
        signals.start_asr_requested.connect(self.show_asr)
        signals.stop_requested.connect(self.hide_all)

    def apply_settings(self, settings: OverlaySettings) -> None:
        """Apply live appearance changes to both mode overlays."""
        self.ocr_overlay.apply_settings(settings)
        self.asr_overlay.apply_settings(settings)

    def show_ocr(self, region: ScreenRegion) -> None:
        """Prepare the OCR translation overlay and hide its ASR peer."""
        self.asr_overlay.hide()
        self.ocr_overlay.set_region(region)

    def show_asr(self, region: ScreenRegion) -> None:
        """Prepare the ASR translation overlay and hide its OCR peer."""
        self.ocr_overlay.hide()
        self.asr_overlay.set_region(region)

    def update_ocr_text(self, text: str, *, speaker: str = "") -> None:
        """Render OCR translation output when its pipeline provides text."""
        self._update_overlay(self.ocr_overlay, text, speaker=speaker)

    def update_asr_text(self, text: str, *, speaker: str = "") -> None:
        """Render ASR translation output when its pipeline provides text."""
        self._update_overlay(self.asr_overlay, text, speaker=speaker)

    def hide_all(self) -> None:
        """Hide and clear overlays when processing stops."""
        for overlay in (self.ocr_overlay, self.asr_overlay):
            overlay.clear_text()
            overlay.hide()

    def hide_ocr(self) -> None:
        """Hide and clear the OCR overlay without affecting ASR."""
        self.ocr_overlay.clear_text()
        self.ocr_overlay.hide()

    def hide_asr(self) -> None:
        """Hide and clear the ASR overlay without affecting OCR."""
        self.asr_overlay.clear_text()
        self.asr_overlay.hide()

    def _show_ocr_from_selection(
        self, subtitle_region: ScreenRegion, translation_region: ScreenRegion
    ) -> None:
        """Use the translation half of an OCR selection for rendered output."""
        del subtitle_region
        self.show_ocr(translation_region)

    @staticmethod
    def _update_overlay(
        overlay: SharedOverlayWindow, text: str, *, speaker: str
    ) -> None:
        overlay.update_text(text, speaker=speaker)
        if text.strip():
            overlay.show()
        else:
            overlay.hide()
