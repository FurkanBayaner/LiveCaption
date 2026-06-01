"""PyQt5 control panel for LiveCaption settings and actions."""

from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path
from ctypes import wintypes

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent, QShowEvent
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import (
    COLOR_PALETTE,
    DEFAULT_BACKGROUND_OPACITY_PERCENT,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE_PX,
    DEFAULT_FONT_WEIGHT_ACTIVE,
    DEFAULT_LETTER_SPACING_PX,
    DEFAULT_LINE_SPACING,
    DEFAULT_SPEAKER_COLOR,
    DEFAULT_TEXT_COLOR,
    DEFAULT_TRANSLATION_ENGINE,
    FONT_FAMILIES,
    FONT_SIZES_PX,
    LETTER_SPACING_OPTIONS_PX,
    LINE_SPACING_OPTIONS,
    TRANSLATION_ENGINES,
)
from core.app_state import AppState
from core.signals import ApplicationSignals
from core.types import OverlaySettings

THEME_PATH = Path(__file__).resolve().parent / "styles" / "theme.qss"
LOGGER = logging.getLogger(__name__)


class JumpSlider(QSlider):
    """Slider that immediately moves to the clicked position."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.width() > 0:
            value = round(
                self.minimum()
                + (self.maximum() - self.minimum()) * event.pos().x() / self.width()
            )
            self.setValue(value)
        super().mousePressEvent(event)


class ControlPanel(QWidget):
    """Fixed-size control panel that emits UI intent through shared signals."""

    def __init__(self, signals: ApplicationSignals) -> None:
        super().__init__()
        self._signals = signals

        self.setObjectName("controlPanel")
        self.setWindowTitle("Live Caption")
        self.setFixedSize(870, 810)

        self._create_controls()
        self._build_layout()
        self._connect_signals()
        self._load_theme()
        self.set_app_state(AppState.IDLE)

    def overlay_settings(self) -> OverlaySettings:
        """Return the currently selected overlay appearance settings."""
        return OverlaySettings(
            font_family=self.font_family_combo.currentText(),
            font_size_px=self._pixel_value(self.font_size_combo),
            letter_spacing_px=self._pixel_value(self.letter_spacing_combo),
            line_spacing=float(self.line_spacing_combo.currentText()),
            font_weight_active=self.font_weight_toggle.isChecked(),
            speaker_color=self.speaker_color_combo.currentText(),
            text_color=self.text_color_combo.currentText(),
            background_opacity_percent=self.opacity_slider.value(),
        )

    def showEvent(self, event: QShowEvent) -> None:
        """Apply Windows title-bar styling after the native window exists."""
        super().showEvent(event)
        self._enable_dark_title_bar()

    def set_app_state(self, state: AppState) -> None:
        """Reflect the Pipeline Manager state without making mode decisions."""
        self.start_ocr_button.setEnabled(state is not AppState.ASR_RUNNING)
        self.start_asr_button.setEnabled(state is not AppState.OCR_RUNNING)

    def _create_controls(self) -> None:
        self.font_family_combo = self._combo(FONT_FAMILIES, DEFAULT_FONT_FAMILY)
        self.font_size_combo = self._combo(FONT_SIZES_PX, DEFAULT_FONT_SIZE_PX, suffix="px")
        self.letter_spacing_combo = self._combo(
            LETTER_SPACING_OPTIONS_PX, DEFAULT_LETTER_SPACING_PX, suffix="px"
        )
        self.line_spacing_combo = self._combo(LINE_SPACING_OPTIONS, DEFAULT_LINE_SPACING)
        self.speaker_color_combo = self._combo(COLOR_PALETTE, DEFAULT_SPEAKER_COLOR)
        self.text_color_combo = self._combo(COLOR_PALETTE, DEFAULT_TEXT_COLOR)
        self.translation_engine_combo = self._combo(
            TRANSLATION_ENGINES, DEFAULT_TRANSLATION_ENGINE
        )

        self.font_weight_toggle = QCheckBox()
        self.font_weight_toggle.setObjectName("fontWeightToggle")
        self.font_weight_toggle.setChecked(DEFAULT_FONT_WEIGHT_ACTIVE)
        self.font_weight_control = self._font_weight_control()

        self.opacity_value_label = QLabel()
        self.opacity_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.opacity_slider = JumpSlider(Qt.Horizontal)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setFixedHeight(46)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(DEFAULT_BACKGROUND_OPACITY_PERCENT)
        self._update_opacity_label(DEFAULT_BACKGROUND_OPACITY_PERCENT)

        self.stop_button = QPushButton("STOP")
        self.stop_button.setObjectName("stopButton")
        self.start_asr_button = QPushButton("START ASR")
        self.start_asr_button.setObjectName("startAsrButton")
        self.start_ocr_button = QPushButton("START OCR")
        self.start_ocr_button.setObjectName("startOcrButton")

    def _build_layout(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 36, 36, 30)
        main_layout.setSpacing(30)

        settings_grid = QGridLayout()
        settings_grid.setHorizontalSpacing(30)
        settings_grid.setVerticalSpacing(27)
        settings_grid.setColumnStretch(0, 1)
        settings_grid.setColumnStretch(1, 1)

        fields = (
            ("Font Family", self.font_family_combo),
            ("Font Size", self.font_size_combo),
            ("Letter Spacing", self.letter_spacing_combo),
            ("Line Spacing", self.line_spacing_combo),
            ("Speaker Color", self.speaker_color_combo),
            ("Text Color", self.text_color_combo),
            ("Font Weight", self.font_weight_control),
            ("Translation", self.translation_engine_combo),
        )
        for index, (label, control) in enumerate(fields):
            settings_grid.addWidget(self._field(label, control), index // 2, index % 2)

        main_layout.addLayout(settings_grid)
        main_layout.addLayout(self._opacity_layout())
        main_layout.addStretch(1)
        main_layout.addLayout(self._button_layout())

    def _connect_signals(self) -> None:
        combos = (
            self.font_family_combo,
            self.font_size_combo,
            self.letter_spacing_combo,
            self.line_spacing_combo,
            self.speaker_color_combo,
            self.text_color_combo,
        )
        for combo in combos:
            combo.currentTextChanged.connect(self._emit_overlay_settings)

        self.font_weight_toggle.toggled.connect(self._emit_overlay_settings)
        self.opacity_slider.valueChanged.connect(self._update_opacity_label)
        self.opacity_slider.valueChanged.connect(self._emit_overlay_settings)

        self.translation_engine_combo.currentTextChanged.connect(
            self._signals.translation_engine_changed
        )
        self.stop_button.clicked.connect(self._signals.stop_requested)
        self.start_asr_button.clicked.connect(self._signals.asr_selection_requested)
        self.start_ocr_button.clicked.connect(self._signals.ocr_selection_requested)
        self._signals.state_changed.connect(self.set_app_state)

    def _load_theme(self) -> None:
        self.setStyleSheet(THEME_PATH.read_text(encoding="utf-8"))

    def _enable_dark_title_bar(self) -> None:
        if sys.platform != "win32":
            return

        enabled = ctypes.c_int(1)
        try:
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            set_window_attribute.argtypes = (
                wintypes.HWND,
                wintypes.DWORD,
                wintypes.LPCVOID,
                wintypes.DWORD,
            )
            set_window_attribute.restype = ctypes.c_long
            for attribute in (20, 19):
                result = set_window_attribute(
                    wintypes.HWND(int(self.winId())),
                    attribute,
                    ctypes.byref(enabled),
                    ctypes.sizeof(enabled),
                )
                if result == 0:
                    return
        except (AttributeError, OSError):
            LOGGER.warning("Windows dark title-bar support is unavailable.")
            return

        LOGGER.warning("Unable to enable the Windows dark title bar.")

    def _emit_overlay_settings(self) -> None:
        self._signals.overlay_settings_changed.emit(self.overlay_settings())

    def _update_opacity_label(self, value: int) -> None:
        self.opacity_value_label.setText(f"%{value}")

    @staticmethod
    def _combo(values: object, default: object, *, suffix: str = "") -> QComboBox:
        combo = QComboBox()
        combo.addItems(f"{value}{suffix}" for value in values)
        combo.setCurrentText(f"{default}{suffix}")
        return combo

    @staticmethod
    def _pixel_value(combo: QComboBox) -> int:
        return int(combo.currentText().removesuffix("px"))

    @staticmethod
    def _field(label: str, control: QWidget) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        field_label = QLabel(label)
        field_label.setObjectName("settingsLabel")
        layout.addWidget(field_label)
        layout.addWidget(control)
        return widget

    def _opacity_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        label = QLabel("Background Opacity")
        label.setObjectName("settingsLabel")
        top_row.addWidget(label)
        top_row.addStretch(1)
        top_row.addWidget(self.opacity_value_label)

        layout.addLayout(top_row)
        layout.addWidget(self.opacity_slider)
        return layout

    def _button_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.start_asr_button)
        layout.addWidget(self.start_ocr_button)
        return layout

    def _font_weight_control(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        active_label = QLabel("Active")
        layout.addWidget(active_label)
        layout.addWidget(self.font_weight_toggle)
        layout.addStretch(1)
        return widget
