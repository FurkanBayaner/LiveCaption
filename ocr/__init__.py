"""OCR capture and recognition adapters."""

from ocr.ocr_engine import OCREngineError, OCRTextResult, WindowsOCREngine
from ocr.screen_capture import ScreenCapture, ScreenCaptureError

__all__ = [
    "OCREngineError",
    "OCRTextResult",
    "ScreenCapture",
    "ScreenCaptureError",
    "WindowsOCREngine",
]
