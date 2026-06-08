"""Screen capture utilities for OCR subtitle regions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import SCREEN_SCALE
from core.types import ScreenRegion


class ScreenCaptureError(RuntimeError):
    """Raised when dxcam cannot capture a usable subtitle frame."""


@dataclass(frozen=True, slots=True)
class CaptureRegion:
    """A dxcam-compatible region in physical pixels."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return the region in the format expected by dxcam."""
        return (self.left, self.top, self.right, self.bottom)


def logical_to_physical_region(
    region: ScreenRegion, device_pixel_ratio: float = 1.0
) -> CaptureRegion:
    """Convert a logical Qt region into the physical-pixel region dxcam expects."""
    if device_pixel_ratio <= 0:
        raise ValueError("Device pixel ratio must be positive.")

    left = round(region.x * device_pixel_ratio)
    top = round(region.y * device_pixel_ratio)
    right = round((region.x + region.width) * device_pixel_ratio)
    bottom = round((region.y + region.height) * device_pixel_ratio)
    if right <= left or bottom <= top:
        raise ValueError("Capture region width and height must be positive.")

    return CaptureRegion(left=left, top=top, right=right, bottom=bottom)


def bgra_to_rgba(frame: Any) -> Any:
    """Convert a dxcam BGRA frame into OCR-ready RGBA bytes."""
    np = _import_numpy()
    if frame.ndim != 3 or frame.shape[2] != 4:
        raise ValueError("Expected a BGRA frame with shape HxWx4.")

    return np.ascontiguousarray(frame[:, :, [2, 1, 0, 3]])


def scale_rgba(frame: Any, scale: float = SCREEN_SCALE) -> Any:
    """Scale an RGBA frame according to the configured OCR scale."""
    np = _import_numpy()
    if scale <= 0:
        raise ValueError("OCR scale must be positive.")
    if scale == 1:
        return np.ascontiguousarray(frame)

    cv2 = _import_cv2()
    height, width = frame.shape[:2]
    target_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(frame, target_size, interpolation=cv2.INTER_CUBIC)


class ScreenCapture:
    """Capture only the selected subtitle region and prepare it for OCR."""

    def __init__(
        self,
        *,
        ocr_scale: float = SCREEN_SCALE,
        device_pixel_ratio: float | None = None,
        camera: Any | None = None,
    ) -> None:
        self._ocr_scale = ocr_scale
        self._device_pixel_ratio = device_pixel_ratio
        self._camera = camera

    @property
    def ocr_scale(self) -> float:
        """Return the configured OCR image scale factor."""
        return self._ocr_scale

    @property
    def device_pixel_ratio_override(self) -> float | None:
        """Return the forced logical-to-physical multiplier, if one was provided."""
        return self._device_pixel_ratio

    def capture(self, region: ScreenRegion) -> Any | None:
        """Return a scaled RGBA frame for the selected subtitle region."""
        device_pixel_ratio = self._device_pixel_ratio or device_pixel_ratio_for_region(
            region
        )
        capture_region = logical_to_physical_region(region, device_pixel_ratio)
        raw_frame = self._capture_bgra(capture_region)
        if raw_frame is None:
            return None

        rgba_frame = bgra_to_rgba(raw_frame)
        return scale_rgba(rgba_frame, self._ocr_scale)

    def close(self) -> None:
        """Release dxcam resources when the pipeline stops."""
        camera = self._camera
        if camera is None:
            return

        stop = getattr(camera, "stop", None)
        if callable(stop):
            stop()
        self._camera = None

    def _capture_bgra(self, region: CaptureRegion) -> Any | None:
        camera = self._get_camera()
        try:
            frame = camera.grab(region=region.as_tuple)
        except Exception as exc:
            raise ScreenCaptureError("Failed to capture selected subtitle region.") from exc

        if frame is None:
            return None
        np = _import_numpy()
        if not isinstance(frame, np.ndarray):
            raise ScreenCaptureError("dxcam returned an unsupported frame type.")
        return frame

    def _get_camera(self) -> Any:
        if self._camera is not None:
            return self._camera

        try:
            import dxcam
        except ImportError as exc:
            raise ScreenCaptureError(
                "dxcam is not installed. Install project requirements before OCR capture."
            ) from exc

        try:
            self._camera = dxcam.create(output_color="BGRA")
        except Exception as exc:
            raise ScreenCaptureError("Failed to create dxcam capture device.") from exc

        if self._camera is None:
            raise ScreenCaptureError("dxcam did not return a capture device.")

        return self._camera


def _import_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise ScreenCaptureError(
            "NumPy is not installed. Install project requirements before OCR capture."
        ) from exc
    return np


def _import_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise ScreenCaptureError(
            "OpenCV is not installed. Install project requirements before OCR scaling."
        ) from exc
    return cv2


def device_pixel_ratio_for_region(region: ScreenRegion) -> float:
    """Best-effort lookup of the Qt screen scale for a logical region."""
    try:
        from PyQt5.QtCore import QPoint
        from PyQt5.QtGui import QGuiApplication
    except ImportError:
        return 1.0

    center = QPoint(region.x + region.width // 2, region.y + region.height // 2)
    screen = QGuiApplication.screenAt(center)
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0

    ratio = float(screen.devicePixelRatio())
    if ratio <= 0:
        return 1.0
    return ratio
