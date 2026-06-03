"""Shared transparent overlay rendering for OCR and ASR modes."""

from __future__ import annotations

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import QWidget

from config import COLOR_PALETTE
from core.types import OverlaySettings, ScreenRegion

_TEXT_PADDING_X = 6.0
_TEXT_PADDING_Y = 3.0
_OVERLAY_MARGIN = 8.0


class SharedOverlayWindow(QWidget):
    """Render translated sentences in a click-through screen region."""

    def __init__(self, settings: OverlaySettings) -> None:
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if hasattr(Qt, "WindowTransparentForInput"):
            flags |= Qt.WindowTransparentForInput

        super().__init__(None, flags)
        self._settings = settings
        self._region: ScreenRegion | None = None
        self._device_pixel_ratio = 1.0
        self._text = ""
        self._speaker = ""

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

    @property
    def device_pixel_ratio(self) -> float:
        """Return the ratio used to map this overlay to capture pixels."""
        return self._device_pixel_ratio

    @property
    def physical_region(self) -> ScreenRegion | None:
        """Return the current logical region converted for pixel-based capture APIs."""
        if self._region is None:
            return None

        ratio = self._device_pixel_ratio
        return ScreenRegion(
            x=round(self._region.x * ratio),
            y=round(self._region.y * ratio),
            width=round(self._region.width * ratio),
            height=round(self._region.height * ratio),
        )

    @classmethod
    def to_physical_region(cls, region: ScreenRegion) -> ScreenRegion:
        """Convert any Qt logical region for pixel-based capture APIs."""
        ratio = cls._ratio_for_region(region)
        return ScreenRegion(
            x=round(region.x * ratio),
            y=round(region.y * ratio),
            width=round(region.width * ratio),
            height=round(region.height * ratio),
        )

    def set_region(self, region: ScreenRegion) -> None:
        """Place the overlay using Qt logical pixels and retain its screen DPI ratio."""
        self._region = region
        self._device_pixel_ratio = self._ratio_for_region(region)
        self.setGeometry(region.x, region.y, region.width, region.height)

    def apply_settings(self, settings: OverlaySettings) -> None:
        """Apply appearance changes immediately without recreating the window."""
        self._settings = settings
        self.update()

    def update_text(self, text: str, *, speaker: str = "") -> None:
        """Replace the rendered sentence and optional speaker label."""
        self._text = text.strip()
        self._speaker = speaker.strip()
        self.update()

    def clear_text(self) -> None:
        """Clear rendered content while keeping the overlay available."""
        self.update_text("")

    def paintEvent(self, event: object) -> None:
        """Draw sentence-sized backgrounds and outlined text."""
        del event
        if not self._text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        font = self._font()
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        lines = self._render_lines(metrics)
        line_height = metrics.height() * self._settings.line_spacing
        baseline = self.height() - _OVERLAY_MARGIN - (len(lines) - 1) * line_height

        for line_index, line in enumerate(lines):
            y = baseline + line_index * line_height
            self._draw_line(painter, metrics, line, y)

    def _draw_line(
        self, painter: QPainter, metrics: QFontMetricsF, line: str, baseline: float
    ) -> None:
        x = _OVERLAY_MARGIN
        speaker_prefix = f"{self._speaker}: " if self._speaker else ""
        line_path = QPainterPath()
        line_path.addText(x, baseline, painter.font(), line)
        bounds = line_path.boundingRect()

        background = QColor("#000000")
        background.setAlphaF(self._settings.background_opacity_percent / 100)
        painter.fillRect(
            bounds.adjusted(
                -_TEXT_PADDING_X,
                -_TEXT_PADDING_Y,
                _TEXT_PADDING_X,
                _TEXT_PADDING_Y,
            ),
            background,
        )

        outline_color = QColor(COLOR_PALETTE[self._settings.text_color]["outline"])
        painter.strokePath(line_path, QPen(outline_color, 1.0))

        if speaker_prefix and line.startswith(speaker_prefix):
            speaker_path = QPainterPath()
            speaker_path.addText(x, baseline, painter.font(), speaker_prefix)
            painter.fillPath(
                speaker_path,
                QColor(COLOR_PALETTE[self._settings.speaker_color]["text"]),
            )
            x += metrics.horizontalAdvance(speaker_prefix)
            text_path = QPainterPath()
            text_path.addText(x, baseline, painter.font(), line.removeprefix(speaker_prefix))
            painter.fillPath(
                text_path, QColor(COLOR_PALETTE[self._settings.text_color]["text"])
            )
            return

        painter.fillPath(line_path, QColor(COLOR_PALETTE[self._settings.text_color]["text"]))

    def _render_lines(self, metrics: QFontMetricsF) -> tuple[str, ...]:
        text = f"{self._speaker}: {self._text}" if self._speaker else self._text
        available_width = max(1.0, self.width() - 2 * _OVERLAY_MARGIN)
        rendered_lines: list[str] = []

        for paragraph in text.splitlines() or [""]:
            words = paragraph.split()
            if not words:
                rendered_lines.append("")
                continue

            current_line = words[0]
            for word in words[1:]:
                candidate = f"{current_line} {word}"
                if metrics.horizontalAdvance(candidate) <= available_width:
                    current_line = candidate
                else:
                    rendered_lines.append(current_line)
                    current_line = word
            rendered_lines.append(current_line)

        return tuple(rendered_lines)

    def _font(self) -> QFont:
        font = QFont(self._settings.font_family)
        font.setPixelSize(self._settings.font_size_px)
        font.setLetterSpacing(QFont.AbsoluteSpacing, self._settings.letter_spacing_px)
        font.setBold(self._settings.font_weight_active)
        return font

    @staticmethod
    def _ratio_for_region(region: ScreenRegion) -> float:
        screen = QGuiApplication.screenAt(
            QPoint(region.x + region.width // 2, region.y + region.height // 2)
        )
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.devicePixelRatio() if screen is not None else 1.0
