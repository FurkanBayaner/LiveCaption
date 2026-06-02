"""LiveCaption application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from logging_config import configure_logging

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication

    from core.pipeline_manager import PipelineManager
    from core.signals import ApplicationSignals
    from ui.control_panel import ControlPanel
    from ui.selection_coordinator import SelectionCoordinator


@dataclass(frozen=True, slots=True)
class RuntimeComponents:
    """Application-owned components that must remain alive during the event loop."""

    signals: ApplicationSignals
    pipeline_manager: PipelineManager
    control_panel: ControlPanel
    selection_coordinator: SelectionCoordinator


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application without initializing feature components."""
    from PyQt5.QtWidgets import QApplication

    return QApplication(list(argv) if argv is not None else sys.argv)


def initialize_components(application: QApplication) -> RuntimeComponents:
    """Create the UI components implemented so far."""
    from core.pipeline_manager import PipelineManager
    from core.signals import ApplicationSignals
    from ui.control_panel import ControlPanel
    from ui.selection_coordinator import SelectionCoordinator

    signals = ApplicationSignals(application)
    pipeline_manager = PipelineManager(
        state_listener=signals.state_changed.emit,
        error_listener=signals.pipeline_error.emit,
    )
    signals.stop_requested.connect(pipeline_manager.stop_active)

    control_panel = ControlPanel(signals)
    control_panel.show()
    selection_coordinator = SelectionCoordinator(signals, control_panel)
    return RuntimeComponents(
        signals=signals,
        pipeline_manager=pipeline_manager,
        control_panel=control_panel,
        selection_coordinator=selection_coordinator,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop."""
    configure_logging()
    application = create_application(argv)
    components = initialize_components(application)
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
