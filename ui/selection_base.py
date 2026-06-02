"""Reusable full-screen region selection behavior."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QGuiApplication, QMouseEvent, QPainter, QPaintEvent
from PyQt5.QtWidgets import QPushButton, QWidget

from core.types import ScreenRegion

MIN_SELECTION_SIZE = 12
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 48
BUTTON_SPACING = 12
BUTTON_MARGIN = 10
THEME_PATH = Path(__file__).resolve().parent / "styles" / "theme.qss"


class SelectionScreenBase(QWidget):
    """Full-screen dimmed selector shared by OCR and ASR screens."""

    selection_confirmed = pyqtSignal(tuple)
    selection_cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._drag_start: QPoint | None = None
        self._primary_region = QRect()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setStyleSheet(THEME_PATH.read_text(encoding="utf-8"))

        self.cancel_button = QPushButton("CANCEL", self)
        self.cancel_button.setObjectName("selectionCancelButton")
        self.cancel_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.cancel_button.clicked.connect(self.cancel_selection)

        self.confirm_button = QPushButton("CONFIRM", self)
        self.confirm_button.setObjectName("selectionConfirmButton")
        self.confirm_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.confirm_button.clicked.connect(self.confirm_selection)

        self._set_buttons_visible(False)

    def open_for_selection(self) -> None:
        """Reset previous state and cover the active screen."""
        self._drag_start = None
        self._primary_region = QRect()
        self._set_buttons_visible(False)

        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.show()
        self.raise_()
        self.activateWindow()
        self.update()

    def cancel_selection(self) -> None:
        """Close the selector without publishing coordinates."""
        self.hide()
        self.selection_cancelled.emit()

    def confirm_selection(self) -> None:
        """Publish valid coordinates and close the selector."""
        if self._primary_region.isNull():
            return

        regions = self.confirmed_regions(self._primary_region)
        self.hide()
        self.selection_confirmed.emit(regions)

    @property
    def has_valid_selection(self) -> bool:
        """Return whether the selected box is large enough to confirm."""
        return (
            self._primary_region.width() >= MIN_SELECTION_SIZE
            and self._primary_region.height() >= MIN_SELECTION_SIZE
        )

    def selection_regions(self, primary_region: QRect) -> tuple[QRect, ...]:
        """Return transparent selection regions for the dimmed backdrop."""
        return (primary_region,)

    def normalize_primary_region(self, primary_region: QRect) -> QRect:
        """Adjust a selected region for mode-specific screen constraints."""
        return primary_region

    def draw_selection_details(self, painter: QPainter, primary_region: QRect) -> None:
        """Draw mode-specific borders and labels."""
        painter.setPen(QColor("#D35400"))
        painter.drawRect(primary_region)

    def confirmed_regions(self, primary_region: QRect) -> tuple[ScreenRegion, ...]:
        """Convert selected rectangles into shared screen coordinates."""
        return (self.to_screen_region(primary_region),)

    def to_screen_region(self, rect: QRect) -> ScreenRegion:
        """Convert a local rectangle to absolute screen coordinates."""
        top_left = self.mapToGlobal(rect.topLeft())
        return ScreenRegion(top_left.x(), top_left.y(), rect.width(), rect.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()
            self._primary_region = QRect(event.pos(), event.pos())
            self._set_buttons_visible(False)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is None:
            return

        self._primary_region = self.normalize_primary_region(
            QRect(self._drag_start, event.pos()).normalized()
        )
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton or self._drag_start is None:
            return

        self._primary_region = self.normalize_primary_region(
            QRect(self._drag_start, event.pos()).normalized()
        )
        self._drag_start = None
        self._set_buttons_visible(self.has_valid_selection)
        if self.has_valid_selection:
            self._position_buttons()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))

        if not self.has_valid_selection:
            return

        painter.save()
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        for region in self.selection_regions(self._primary_region):
            painter.fillRect(region, QColor(0, 0, 0, 1))
        painter.restore()

        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_selection_details(painter, self._primary_region)

    def _position_buttons(self) -> None:
        total_width = BUTTON_WIDTH * 2 + BUTTON_SPACING
        desired_x = self._primary_region.right() - total_width
        desired_y = self._primary_region.bottom() + BUTTON_MARGIN

        x = max(BUTTON_MARGIN, min(desired_x, self.width() - total_width - BUTTON_MARGIN))
        y = max(BUTTON_MARGIN, min(desired_y, self.height() - BUTTON_HEIGHT - BUTTON_MARGIN))

        self.cancel_button.move(x, y)
        self.confirm_button.move(x + BUTTON_WIDTH + BUTTON_SPACING, y)

    def _set_buttons_visible(self, visible: bool) -> None:
        self.cancel_button.setVisible(visible)
        self.confirm_button.setVisible(visible)
