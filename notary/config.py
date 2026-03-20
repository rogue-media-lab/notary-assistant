"""Config layer — reads/writes ~/.notary_assistant/config.json."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".notary_assistant"
CONFIG_FILE = CONFIG_DIR / "config.json"
EXPORTS_DIR = CONFIG_DIR / "exports"

DEFAULTS = {
    "gemini_api_key": "",
    "gemini_model": "gemini-2.5-flash",
    "business_name": "Stamp and Certify Co",
    "legal_entity": "Roberts and Associates LLC",
    "notary_name": "",
    "commission_number": "",
    "commission_expires": "",  # ISO format: YYYY-MM-DD
    "county": "",
    "travel_fee_default": 0.0,
}


def load() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        for k, v in DEFAULTS.items():
            data.setdefault(k, v)
        return data
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def is_configured() -> bool:
    """Returns True if a Gemini API key has been saved."""
    return CONFIG_FILE.exists() and bool(load().get("gemini_api_key"))


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_gemini_key() -> str:
    """Return API key from environment variable or config file."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        key = load().get("gemini_api_key", "")
    return key
