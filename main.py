"""LiveCaption application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

from logging_config import configure_logging

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application without initializing feature components."""
    from PyQt5.QtWidgets import QApplication

    return QApplication(list(argv) if argv is not None else sys.argv)


def initialize_components(application: QApplication) -> None:
    """Wire runtime components as their implementation issues land."""
    del application


def main(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop."""
    configure_logging()
    application = create_application(argv)
    initialize_components(application)
    return application.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
