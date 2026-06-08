"""Shared Qt signals for communication between UI and runtime components."""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal


class ApplicationSignals(QObject):
    """Signals emitted by the control panel and Pipeline Manager."""

    ocr_selection_requested = pyqtSignal()
    asr_selection_requested = pyqtSignal()
    start_ocr_requested = pyqtSignal(object, object)
    start_asr_requested = pyqtSignal(object)
    stop_requested = pyqtSignal()
    ocr_debug_preview_requested = pyqtSignal()
    ocr_translation_ready = pyqtSignal(str)
    ocr_overlay_clear_requested = pyqtSignal()
    ocr_pipeline_finished = pyqtSignal()
    overlay_settings_changed = pyqtSignal(object)
    translation_engine_changed = pyqtSignal(str)
    translation_engine_switch_failed = pyqtSignal(str, str)

    state_changed = pyqtSignal(object)
    pipeline_error = pyqtSignal(str)
