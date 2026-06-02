"""Coordinate selection screens without embedding pipeline decisions in the UI."""

from __future__ import annotations

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget

from core.signals import ApplicationSignals
from ui.asr.asr_selection_screen import AsrSelectionScreen
from ui.ocr.ocr_selection_screen import OcrSelectionScreen


class SelectionCoordinator(QObject):
    """Open mode-specific selectors and forward confirmed coordinates."""

    def __init__(self, signals: ApplicationSignals, control_panel: QWidget) -> None:
        super().__init__(control_panel)
        self._signals = signals
        self._control_panel = control_panel
        self._ocr_screen = OcrSelectionScreen()
        self._asr_screen = AsrSelectionScreen()

        signals.ocr_selection_requested.connect(self.open_ocr_selection)
        signals.asr_selection_requested.connect(self.open_asr_selection)
        self._ocr_screen.selection_confirmed.connect(self._confirm_ocr)
        self._asr_screen.selection_confirmed.connect(self._confirm_asr)
        self._ocr_screen.selection_cancelled.connect(self._restore_control_panel)
        self._asr_screen.selection_cancelled.connect(self._restore_control_panel)

    def open_ocr_selection(self) -> None:
        """Minimize the control panel and open OCR region selection."""
        self._control_panel.showMinimized()
        self._ocr_screen.open_for_selection()

    def open_asr_selection(self) -> None:
        """Minimize the control panel and open ASR overlay selection."""
        self._control_panel.showMinimized()
        self._asr_screen.open_for_selection()

    def _confirm_ocr(self, regions: tuple[object, ...]) -> None:
        subtitle_region, translation_region = regions
        self._signals.start_ocr_requested.emit(subtitle_region, translation_region)

    def _confirm_asr(self, regions: tuple[object, ...]) -> None:
        (translation_region,) = regions
        self._signals.start_asr_requested.emit(translation_region)

    def _restore_control_panel(self) -> None:
        self._control_panel.showNormal()
        self._control_panel.raise_()
        self._control_panel.activateWindow()
