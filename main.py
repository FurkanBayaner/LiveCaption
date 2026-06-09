"""LiveCaption application entry point."""

from __future__ import annotations

import sys
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from logging_config import configure_logging

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication

    from core.pipeline_manager import PipelineManager
    from core.signals import ApplicationSignals
    from asr.asr_pipeline import ASRPipeline
    from ui.control_panel import ControlPanel
    from ui.ocr.ocr_debug_coordinator import OCRDebugCoordinator
    from ui.overlay_coordinator import OverlayCoordinator
    from ui.selection_coordinator import SelectionCoordinator
    from translation.translation_router import TranslationRouter


@dataclass(frozen=True, slots=True)
class RuntimeComponents:
    """Application-owned components that must remain alive during the event loop."""

    signals: ApplicationSignals
    pipeline_manager: PipelineManager
    control_panel: ControlPanel
    selection_coordinator: SelectionCoordinator
    overlay_coordinator: OverlayCoordinator
    ocr_debug_coordinator: OCRDebugCoordinator
    translation_router: TranslationRouter


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application without initializing feature components."""
    from PyQt5.QtWidgets import QApplication

    return QApplication(list(argv) if argv is not None else sys.argv)


def initialize_components(application: QApplication) -> RuntimeComponents:
    """Create the UI components implemented so far."""
    from core.pipeline_manager import PipelineManager
    from core.signals import ApplicationSignals
    from asr.asr_pipeline import ASRPipeline
    from ui.control_panel import ControlPanel
    from ui.ocr.ocr_debug_coordinator import OCRDebugCoordinator
    from ui.overlay_coordinator import OverlayCoordinator
    from ui.selection_coordinator import SelectionCoordinator
    from ocr.ocr_pipeline import OCRPipeline
    from translation.translation_router import TranslationRouter

    signals = ApplicationSignals(application)
    pipeline_manager = PipelineManager(
        state_listener=signals.state_changed.emit,
        error_listener=signals.pipeline_error.emit,
    )
    signals.stop_requested.connect(pipeline_manager.stop_active)
    signals.ocr_pipeline_finished.connect(pipeline_manager.stop_active)
    signals.asr_pipeline_finished.connect(pipeline_manager.stop_active)

    control_panel = ControlPanel(signals)
    control_panel.show()
    selection_coordinator = SelectionCoordinator(signals, control_panel)
    overlay_coordinator = OverlayCoordinator(signals, control_panel.overlay_settings())
    ocr_debug_coordinator = OCRDebugCoordinator(signals)
    translation_router = TranslationRouter(error_listener=signals.pipeline_error.emit)

    def switch_translation_engine(display_name: str) -> None:
        changed = translation_router.switch_engine(display_name)
        active_engine = translation_router.active_engine_name
        if not changed and active_engine != display_name:
            signals.translation_engine_switch_failed.emit(active_engine, display_name)

    signals.translation_engine_changed.connect(switch_translation_engine)

    def start_ocr_pipeline(subtitle_region: object, translation_region: object) -> None:
        try:
            del translation_region
            was_busy = pipeline_manager.active_mode is not None
            pipeline = OCRPipeline(
                subtitle_region=subtitle_region,
                translation_router=translation_router,
                text_listener=signals.ocr_translation_ready.emit,
                error_listener=signals.pipeline_error.emit,
                stop_listener=signals.ocr_overlay_clear_requested.emit,
                finish_listener=signals.ocr_pipeline_finished.emit,
            )
            started = pipeline_manager.start_ocr(pipeline)
            if started or was_busy:
                return
            signals.ocr_overlay_clear_requested.emit()
        except Exception as exc:
            LOGGER.exception("Failed to start OCR pipeline.")
            signals.ocr_overlay_clear_requested.emit()
            signals.pipeline_error.emit(f"Failed to start OCR pipeline: {exc}")

    signals.start_ocr_requested.connect(start_ocr_pipeline)

    def start_asr_pipeline(translation_region: object) -> None:
        try:
            del translation_region
            was_busy = pipeline_manager.active_mode is not None
            pipeline = ASRPipeline(
                translation_router=translation_router,
                text_listener=signals.asr_translation_ready.emit,
                error_listener=signals.pipeline_error.emit,
                stop_listener=signals.asr_overlay_clear_requested.emit,
                finish_listener=signals.asr_pipeline_finished.emit,
            )
            started = pipeline_manager.start_asr(pipeline)
            if started or was_busy:
                return
            signals.asr_overlay_clear_requested.emit()
        except Exception as exc:
            LOGGER.exception("Failed to start ASR pipeline.")
            signals.asr_overlay_clear_requested.emit()
            signals.pipeline_error.emit(f"Failed to start ASR pipeline: {exc}")

    signals.start_asr_requested.connect(start_asr_pipeline)
    return RuntimeComponents(
        signals=signals,
        pipeline_manager=pipeline_manager,
        control_panel=control_panel,
        selection_coordinator=selection_coordinator,
        overlay_coordinator=overlay_coordinator,
        ocr_debug_coordinator=ocr_debug_coordinator,
        translation_router=translation_router,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop."""
    configure_logging()
    application = create_application(argv)
    components = initialize_components(application)
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
