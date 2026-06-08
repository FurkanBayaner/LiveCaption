"""OCR capture and recognition adapters."""

from ocr.ocr_engine import OCREngineError, OCRTextResult, WindowsOCREngine
from ocr.ocr_memory import OCRMemory
from ocr.ocr_pipeline import OCRPipeline
from ocr.screen_capture import ScreenCapture, ScreenCaptureError

__all__ = [
    "OCREngineError",
    "OCRMemory",
    "OCRPipeline",
    "OCRTextResult",
    "ScreenCapture",
    "ScreenCaptureError",
    "WindowsOCREngine",
]
