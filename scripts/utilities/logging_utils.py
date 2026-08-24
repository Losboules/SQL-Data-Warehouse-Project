"""Consistent, non-secret logging for Northstar Retail scripts."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def configure_logging(*, log_file: str | Path | None = None) -> None:
    """Configure console logging once and optionally add a UTF-8 file handler."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()

    if not root.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(
            logging.Formatter(
                fmt="%(asctime)sZ | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        root.addHandler(console)
    root.setLevel(level)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve()
        if not any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename).resolve() == resolved
            for handler in root.handlers
        ):
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)sZ | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
            root.addHandler(file_handler)
