"""
app/utils/logger.py
────────────────────
Centralised logging configuration using Loguru.
All modules should import `logger` from this module instead of using the
standard-library `logging` directly.

Usage:
    from app.utils.logger import logger

    logger.info("Server starting on port {port}", port=8000)
    logger.error("Something went wrong: {error}", error=exc)
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger  # noqa: F401  (re-exported)

from app.config import get_settings


def configure_logging() -> None:
    """
    Configure Loguru sinks.

    - Console sink: colourised, human-readable output.
    - File sink: structured rotation with retention policy.

    Call this once at application startup (inside `lifespan` in main.py).
    """
    settings = get_settings()

    # Remove the default Loguru handler so we control all output.
    logger.remove()

    # ── Console Sink ─────────────────────────────────────────────────────────
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # ── File Sink ─────────────────────────────────────────────────────────────
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        format=log_format,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=settings.debug,
        enqueue=True,   # thread-safe async writes
    )

    logger.info(
        "Logging configured | level={level} | file={file}",
        level=settings.log_level,
        file=settings.log_file,
    )
