"""
Centralized logging configuration for Tretra Trading Station
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "tretra",
    level: int = logging.INFO,
    log_dir: str = "/app/logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers

    Args:
        name: Logger name
        level: Logging level
        log_dir: Directory for log files
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs to root logger

    # Log format
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")

    return logger


# Pre-configured loggers for different components
def get_screening_logger() -> logging.Logger:
    """Get logger for screening service"""
    return setup_logger("tretra.screening")


def get_monitor_logger() -> logging.Logger:
    """Get logger for monitor service"""
    return setup_logger("tretra.monitor")


def get_trading_logger() -> logging.Logger:
    """Get logger for trading service"""
    return setup_logger("tretra.trading")


def get_api_logger() -> logging.Logger:
    """Get logger for API routes"""
    return setup_logger("tretra.api")


# Default logger
default_logger = setup_logger()
