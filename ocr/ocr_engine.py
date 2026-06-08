"""Windows.Media.Ocr adapter for OCR-ready RGBA frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class OCREngineError(RuntimeError):
    """Raised when Windows OCR cannot be initialized or used."""


@dataclass(frozen=True, slots=True)
class OCRTextResult:
    """Plain text returned by the OCR engine."""

    text: str

    @property
    def is_empty(self) -> bool:
        """Return whether this result can be skipped by the OCR pipeline."""
        return self.text == ""


def normalize_ocr_text(lines: list[str]) -> str:
    """Normalize OCR lines into the plain text format consumed by the pipeline."""
    return "\n".join(line.strip() for line in lines if line.strip()).strip()


class WindowsOCREngine:
    """Read plain text from RGBA images using Windows.Media.Ocr."""

    def __init__(self, language_tag: str | None = None) -> None:
        self._language_tag = language_tag
        self._engine: Any | None = None
        self._imports: dict[str, Any] | None = None

    @property
    def language_tag(self) -> str | None:
        """Return the requested Windows OCR language tag, if one was set."""
        return self._language_tag

    async def recognize(self, rgba_frame: Any) -> OCRTextResult:
        """Return normalized OCR text for an RGBA frame."""
        _validate_rgba_frame(rgba_frame)
        if rgba_frame.size == 0:
            return OCRTextResult("")

        bitmap = await self._rgba_to_software_bitmap(rgba_frame)
        try:
            result = await self._get_engine().recognize_async(bitmap)
        except Exception as exc:
            raise OCREngineError("Windows OCR failed to recognize the frame.") from exc

        lines = [line.text for line in getattr(result, "lines", [])]
        return OCRTextResult(normalize_ocr_text(lines))

    async def recognize_text(self, rgba_frame: Any) -> str:
        """Return only the normalized OCR text for callers that do not need metadata."""
        return (await self.recognize(rgba_frame)).text

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine

        imports = self._load_imports()
        ocr_engine = imports["OcrEngine"]

        if self._language_tag is None:
            engine = ocr_engine.try_create_from_user_profile_languages()
        else:
            language = imports["Language"](self._language_tag)
            engine = ocr_engine.try_create_from_language(language)

        if engine is None:
            raise OCREngineError("Windows OCR engine is not available for this language.")

        self._engine = engine
        return self._engine

    async def _rgba_to_software_bitmap(self, rgba_frame: Any) -> Any:
        imports = self._load_imports()
        png_bytes = _encode_rgba_png(rgba_frame)

        try:
            stream = imports["InMemoryRandomAccessStream"]()
            writer = imports["DataWriter"](stream)
            writer.write_bytes(png_bytes)
            await writer.store_async()
            await writer.flush_async()
            writer.detach_stream()
            stream.seek(0)

            decoder = await imports["BitmapDecoder"].create_async(stream)
            return await decoder.get_software_bitmap_async(
                _enum_value(imports["BitmapPixelFormat"], "RGBA8", "rgba8"),
                _enum_value(
                    imports["BitmapAlphaMode"], "PREMULTIPLIED", "premultiplied"
                ),
            )
        except Exception as exc:
            raise OCREngineError("Failed to prepare OCR frame for Windows OCR.") from exc

    def _load_imports(self) -> dict[str, Any]:
        if self._imports is not None:
            return self._imports

        try:
            from winrt.windows.globalization import Language
            from winrt.windows.graphics.imaging import (
                BitmapAlphaMode,
                BitmapDecoder,
                BitmapPixelFormat,
            )
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
        except ImportError as exc:
            raise OCREngineError(
                "Windows OCR dependencies are not installed. Install project requirements before OCR."
            ) from exc

        self._imports = {
            "BitmapAlphaMode": BitmapAlphaMode,
            "BitmapDecoder": BitmapDecoder,
            "BitmapPixelFormat": BitmapPixelFormat,
            "DataWriter": DataWriter,
            "InMemoryRandomAccessStream": InMemoryRandomAccessStream,
            "Language": Language,
            "OcrEngine": OcrEngine,
        }
        return self._imports


def _encode_rgba_png(rgba_frame: Any) -> bytes:
    """Encode an RGBA frame as PNG bytes for WinRT bitmap decoding."""
    cv2 = _import_cv2()
    np = _import_numpy()
    rgba_frame = np.ascontiguousarray(rgba_frame)
    bgra_frame = cv2.cvtColor(rgba_frame, cv2.COLOR_RGBA2BGRA)
    success, encoded = cv2.imencode(".png", bgra_frame)
    if not success:
        raise OCREngineError("Failed to encode OCR frame for Windows OCR.")
    return encoded.tobytes()


def _validate_rgba_frame(rgba_frame: Any) -> None:
    missing_attributes = [
        name
        for name in ("size", "ndim", "shape")
        if not hasattr(rgba_frame, name)
    ]
    if missing_attributes:
        raise ValueError("Windows OCR expects a NumPy-like RGBA frame.")
    if rgba_frame.ndim != 3 or rgba_frame.shape[2] != 4:
        raise ValueError("Windows OCR expects an RGBA frame with shape HxWx4.")


def _enum_value(enum_type: Any, *names: str) -> Any:
    for name in names:
        if hasattr(enum_type, name):
            return getattr(enum_type, name)
    raise OCREngineError(f"Windows OCR enum value is unavailable: {', '.join(names)}")


def _import_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise OCREngineError(
            "NumPy is not installed. Install project requirements before OCR."
        ) from exc
    return np


def _import_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise OCREngineError(
            "OpenCV is not installed. Install project requirements before OCR."
        ) from exc
    return cv2
