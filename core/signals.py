"""Shared Qt signals for communication between UI and runtime components."""

from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal


class ApplicationSignals(QObject):
    """Signals emitted by the control panel and Pipeline Manager."""

    start_ocr_requested = pyqtSignal(object, object)
    start_asr_requested = pyqtSignal(object)
    stop_requested = pyqtSignal()
    overlay_settings_changed = pyqtSignal(object)

    state_changed = pyqtSignal(object)
    pipeline_error = pyqtSignal(str)
