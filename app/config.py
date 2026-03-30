"""
Configuration module for Deanta API.
Loads settings from environment variables with sensible defaults.
"""

import os
import logging


# ---------- SERVER CONFIG ----------
HOST = os.getenv("DEANTA_HOST", "0.0.0.0")
PORT = int(os.getenv("DEANTA_PORT", "8000"))
DEBUG = os.getenv("DEANTA_DEBUG", "false").lower() in ("true", "1", "yes")

# ---------- LOGGING CONFIG ----------
LOG_LEVEL = os.getenv("DEANTA_LOG_LEVEL", "INFO").upper()


def setup_logging():
    """Configure logging with console output only."""
    logger = logging.getLogger("deanta")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()
