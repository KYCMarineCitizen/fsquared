from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_path: Path) -> logging.Logger:
    """
    Configure application-wide logging.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("email_service")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers when running in reload/debug contexts.
    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == str(log_path) for handler in logger.handlers):
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        logger.addHandler(stream_handler)

    return logger

