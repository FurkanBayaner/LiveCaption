"""Logging setup for LiveCaption runtime diagnostics."""

from __future__ import annotations

import logging
from pathlib import Path

from config import APP_LOG_PATH

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_path: Path = APP_LOG_PATH) -> None:
    """Configure console and file logging for the application."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=(file_handler, console_handler),
        force=True,
    )
