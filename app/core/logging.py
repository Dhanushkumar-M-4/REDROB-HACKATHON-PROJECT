"""AI Smart Candidate Ranking System - Logging Setup with Loguru."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/ranking_system.log") -> None:
    """Configure Loguru with console and file sinks.

    Args:
        log_level: Minimum log level to capture.
        log_file: Path to the log file (relative to project root).
    """
    # Remove default logger
    logger.remove()

    # Configure level icons for the hackathon UI
    logger.level("TRACE", icon="🔍")
    logger.level("DEBUG", icon="🐛")
    logger.level("INFO", icon="✨")
    logger.level("SUCCESS", icon="✅")
    logger.level("WARNING", icon="⚠️")
    logger.level("ERROR", icon="❌")
    logger.level("CRITICAL", icon="🔥")

    # ── Console Sink ───────────────────────────────────────────────
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:HH:mm:ss}</green> │ "
            "<level>{level.icon} {level: <8}</level> │ "
            "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> │ "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # ── File Sink ──────────────────────────────────────────────────
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        level=log_level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} │ "
            "{level: <8} │ "
            "{module}:{function}:{line} │ "
            "{message}"
        ),
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe
    )

    logger.info("Logging initialized │ level={} │ file={}", log_level, log_file)


def get_logger():
    """Return the configured Loguru logger instance."""
    return logger
