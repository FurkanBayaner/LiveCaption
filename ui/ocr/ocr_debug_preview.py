"""Live OCR debug preview window for a logical screen region."""

from __future__ import annotations

from PyQt5.QtCore import QEvent, QPoint, QRect, QTimer, Qt
from PyQt5.QtGui import QGuiApplication, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from core.types import ScreenRegion

_FRAME_INTERVAL_MS = 33


class OCRDebugPreview(QWidget):
    """Show a live preview of a logical screen region in its own window."""

    def __init__(self, region: ScreenRegion | None = None) -> None:
        super().__init__(None, Qt.Window)
        self._region: ScreenRegion | None = None
        self._frame = QPixmap()

        self.setObjectName("ocrDebugPreview")
        self.setWindowTitle("OCR Debug Preview")
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._image_label.setStyleSheet("background-color: #000;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._image_label)
        self.setLayout(layout)

        self._timer = QTimer(self)
        self._timer.setInterval(_FRAME_INTERVAL_MS)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._refresh_frame)

        if region is not None:
            self.set_region(region)

    @property
    def region(self) -> ScreenRegion | None:
        """Return the currently previewed logical region."""
        return self._region

    def set_region(self, region: ScreenRegion) -> None:
        """Update the previewed logical region and resize the window to match it."""
        self._region = region
        self.setFixedSize(region.width, region.height)
        self._image_label.setFixedSize(region.width, region.height)

    def place_away_from_source(self) -> None:
        """Move the preview away from its source region when screen space allows."""
        region = self._region
        if region is None:
            return

        source_rect = QRect(region.x, region.y, region.width, region.height)
        screen = QGuiApplication.screenAt(self._source_center(region))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        frame_size = self.frameSize()
        width = max(frame_size.width(), self.width())
        height = max(frame_size.height(), self.height())
        margin = 16
        candidates = (
            QPoint(source_rect.right() + margin, source_rect.top()),
            QPoint(source_rect.left() - width - margin, source_rect.top()),
            QPoint(source_rect.left(), source_rect.bottom() + margin),
            QPoint(source_rect.left(), source_rect.top() - height - margin),
            available.topLeft(),
            QPoint(available.right() - width + 1, available.top()),
            QPoint(available.left(), available.bottom() - height + 1),
            QPoint(available.right() - width + 1, available.bottom() - height + 1),
        )
        for point in candidates:
            preview_rect = QRect(point, frame_size)
            if available.contains(preview_rect) and not preview_rect.intersects(source_rect):
                self.move(point)
                return

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        self._start_timer_if_needed()

    def hideEvent(self, event: object) -> None:
        self._stop_timer()
        super().hideEvent(event)

    def closeEvent(self, event: object) -> None:
        self._stop_timer()
        super().closeEvent(event)

    def changeEvent(self, event: object) -> None:
        if isinstance(event, QEvent) and event.type() == QEvent.WindowStateChange:
            if self._should_capture():
                self._start_timer_if_needed()
                self._refresh_frame()
            else:
                self._stop_timer()
        super().changeEvent(event)

    def moveEvent(self, event: object) -> None:
        super().moveEvent(event)
        if self._should_capture():
            self._start_timer_if_needed()
        else:
            self._stop_timer()

    def _start_timer_if_needed(self) -> None:
        if self._should_capture() and not self._timer.isActive():
            self._timer.start()

    def _stop_timer(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

    def _should_capture(self) -> bool:
        return (
            self._region is not None
            and self.isVisible()
            and not self.isMinimized()
            and not self._overlaps_source()
        )

    def _overlaps_source(self) -> bool:
        region = self._region
        if region is None:
            return False
        source_rect = QRect(region.x, region.y, region.width, region.height)
        return self.frameGeometry().intersects(source_rect)

    def _refresh_frame(self) -> None:
        region = self._region
        if region is None:
            return

        if not self._should_capture():
            self._stop_timer()
            return

        screen = QGuiApplication.screenAt(
            self._source_center(region)
        )
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        screen_geometry = screen.geometry()
        pixmap = screen.grabWindow(
            0,
            region.x - screen_geometry.x(),
            region.y - screen_geometry.y(),
            region.width,
            region.height,
        )
        if pixmap.isNull():
            return

        if pixmap.size() != self._image_label.size():
            pixmap = pixmap.scaled(
                self._image_label.size(),
                Qt.IgnoreAspectRatio,
                Qt.FastTransformation,
            )

        self._frame = pixmap
        self._image_label.setPixmap(self._frame)

    @staticmethod
    def _source_center(region: ScreenRegion) -> QPoint:
        return QPoint(region.x + region.width // 2, region.y + region.height // 2)
