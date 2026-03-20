"""Application logging — writes to ~/.notary_assistant/app.log."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config as cfg

LOG_FILE = cfg.CONFIG_DIR / "app.log"
_configured = False


def get_logger(name: str = "notary") -> logging.Logger:
    """Return a logger, configuring handlers on first call."""
    global _configured
    logger = logging.getLogger(name)

    if not _configured:
        cfg.ensure_dirs()
        logger.setLevel(logging.DEBUG)

        # Rotating file: max 1 MB, keep 3 backups
        fh = RotatingFileHandler(
            str(LOG_FILE), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(fh)
        _configured = True

    return logger


def read_recent(lines: int = 100) -> str:
    """Return the last N lines of the log file as a string."""
    if not LOG_FILE.exists():
        return "(No log file yet.)"
    with open(LOG_FILE, encoding="utf-8") as f:
        all_lines = f.readlines()
    return "".join(all_lines[-lines:])
