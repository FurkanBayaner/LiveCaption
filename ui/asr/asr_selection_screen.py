"""ASR selection screen implementation."""

from __future__ import annotations

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen

from core.types import ScreenRegion
from ui.selection_base import SelectionScreenBase


class AsrSelectionScreen(SelectionScreenBase):
    """Selection screen that captures only the translation overlay region."""

    _TRANSLATION_COLOR = QColor("#D35400")
    _LABEL_BACKGROUND = QColor(44, 62, 80, 230)
    _LABEL_PADDING_X = 12
    _LABEL_PADDING_Y = 8

    def selection_regions(self, primary_region: QRect) -> tuple[QRect, ...]:
        return (QRect(primary_region),)

    def draw_selection_details(self, painter: QPainter, primary_region: QRect) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        pen = QPen(self._TRANSLATION_COLOR)
        pen.setWidthF(2.5)
        painter.setPen(pen)
        painter.drawRect(primary_region)

        self._draw_label(painter, primary_region.topLeft())
        painter.restore()

    def confirmed_regions(self, primary_region: QRect) -> tuple[ScreenRegion, ...]:
        return (self.to_screen_region(primary_region),)

    def _draw_label(self, painter: QPainter, anchor: QPoint) -> None:
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        label_text = "TRANSLATION"
        text_width = metrics.horizontalAdvance(label_text)
        text_height = metrics.height()

        label_width = self._LABEL_PADDING_X * 2 + text_width
        label_height = text_height + self._LABEL_PADDING_Y * 2
        label_rect = QRect(anchor.x(), anchor.y() - label_height - 8, label_width, label_height)
        if label_rect.top() < 0:
            label_rect.moveTop(anchor.y() + 8)
        if label_rect.right() > self.width():
            label_rect.moveRight(self.width())

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._LABEL_BACKGROUND)
        painter.drawRoundedRect(label_rect, 6, 6)

        baseline_y = label_rect.top() + self._LABEL_PADDING_Y + metrics.ascent()
        text_x = label_rect.left() + self._LABEL_PADDING_X

        painter.setPen(self._TRANSLATION_COLOR)
        painter.drawText(text_x, baseline_y, label_text)
