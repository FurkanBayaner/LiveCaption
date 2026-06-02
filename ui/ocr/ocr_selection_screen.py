"""OCR selection screen implementation."""

from __future__ import annotations

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter

from core.types import ScreenRegion
from ui.selection_base import SelectionScreenBase


class OcrSelectionScreen(SelectionScreenBase):
    """Selection screen that captures subtitle and translation regions."""

    _BORDER_THICKNESS = 2
    _SUBTITLE_COLOR = QColor("#2980B9")
    _TRANSLATION_COLOR = QColor("#D35400")
    _LABEL_BACKGROUND = QColor(44, 62, 80, 230)
    _LABEL_TEXT = "SUBTITLE - TRANSLATION"
    _LABEL_PADDING_X = 12
    _LABEL_PADDING_Y = 8
    _LABEL_GAP = 6

    def normalize_primary_region(self, primary_region: QRect) -> QRect:
        region = QRect(primary_region)
        if region.isNull():
            return region

        max_height = self._max_primary_height(region)
        if region.height() > max_height:
            if self._drag_start is not None and self._drag_start.y() == region.bottom():
                region.setTop(region.bottom() - max_height + 1)
            else:
                region.setBottom(region.top() + max_height - 1)
        return region.intersected(self.rect())

    def selection_regions(self, primary_region: QRect) -> tuple[QRect, ...]:
        translation_region = QRect(
            primary_region.x(),
            primary_region.y() - primary_region.height(),
            primary_region.width(),
            primary_region.height(),
        )
        subtitle_region = QRect(primary_region)
        return subtitle_region, translation_region

    def draw_selection_details(self, painter: QPainter, primary_region: QRect) -> None:
        subtitle_region, translation_region = self.selection_regions(primary_region)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        self._draw_region_outline(painter, subtitle_region, self._SUBTITLE_COLOR)
        self._draw_region_outline(painter, translation_region, self._TRANSLATION_COLOR)

        self._draw_label(painter, translation_region.topLeft())
        painter.restore()

    def confirmed_regions(self, primary_region: QRect) -> tuple[ScreenRegion, ...]:
        subtitle_region, translation_region = self.selection_regions(primary_region)
        return (
            self.to_screen_region(subtitle_region),
            self.to_screen_region(translation_region),
        )

    def _draw_label(self, painter: QPainter, anchor: QPoint) -> None:
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        subtitle_text = "SUBTITLE"
        dash_text = "-"
        translation_text = "TRANSLATION"

        subtitle_width = metrics.horizontalAdvance(subtitle_text)
        dash_width = metrics.horizontalAdvance(dash_text)
        translation_width = metrics.horizontalAdvance(translation_text)
        text_height = metrics.height()

        label_width = (
            self._LABEL_PADDING_X * 2
            + subtitle_width
            + dash_width
            + translation_width
            + self._LABEL_GAP * 2
        )
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

        painter.setPen(self._SUBTITLE_COLOR)
        painter.drawText(text_x, baseline_y, subtitle_text)
        text_x += subtitle_width + self._LABEL_GAP

        painter.setPen(Qt.white)
        painter.drawText(text_x, baseline_y, dash_text)
        text_x += dash_width + self._LABEL_GAP

        painter.setPen(self._TRANSLATION_COLOR)
        painter.drawText(text_x, baseline_y, translation_text)

    def _max_primary_height(self, primary_region: QRect) -> int:
        if self._drag_start is not None and self._drag_start.y() == primary_region.bottom():
            return max(1, (primary_region.bottom() + 1) // 2)
        return max(1, primary_region.top())

    def _draw_region_outline(self, painter: QPainter, region: QRect, color: QColor) -> None:
        thickness = min(self._BORDER_THICKNESS, region.width(), region.height())
        if thickness <= 0:
            return

        painter.fillRect(region.left(), region.top(), region.width(), thickness, color)
        painter.fillRect(
            region.left(),
            region.bottom() - thickness + 1,
            region.width(),
            thickness,
            color,
        )
        painter.fillRect(region.left(), region.top(), thickness, region.height(), color)
        painter.fillRect(
            region.right() - thickness + 1,
            region.top(),
            thickness,
            region.height(),
            color,
        )
