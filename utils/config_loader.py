"""Helpers for loading and normalizing DigitalFTE runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VAULT = ROOT / "vault"


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _resolve_vault_path(raw: str | None) -> Path:
    if not raw:
        return DEFAULT_VAULT

    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate
    return (ROOT / candidate).resolve()


def load_config(dotenv_path: str | Path | None = None) -> dict[str, Any]:
    """Load .env values and return normalized runtime settings."""
    load_dotenv(dotenv_path=dotenv_path, override=dotenv_path is not None)

    return {
        "CONTROL_CENTER_PORT": _int_env("CONTROL_CENTER_PORT", 8282),
        "DRY_RUN": _bool_env("DRY_RUN", default=False),
        "GMAIL_CLIENT_ID": os.getenv("GMAIL_CLIENT_ID"),
        "GMAIL_CLIENT_SECRET": os.getenv("GMAIL_CLIENT_SECRET"),
        "LINKEDIN_ACCESS_TOKEN": os.getenv("LINKEDIN_ACCESS_TOKEN"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "MAX_RETRY_ATTEMPTS": _int_env("MAX_RETRY_ATTEMPTS", 3),
        "META_APP_SECRET": os.getenv("META_APP_SECRET"),
        "MODEL_ID": os.getenv("MODEL_ID", "amazon.nova-lite-v1:0"),
        "ODOO_DB": os.getenv("ODOO_DB"),
        "ODOO_PASSWORD": os.getenv("ODOO_PASSWORD"),
        "ODOO_URL": os.getenv("ODOO_URL"),
        "ODOO_USERNAME": os.getenv("ODOO_USERNAME"),
        "STRANDS_CHAT_URL": os.getenv("STRANDS_CHAT_URL"),
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "TWILIO_WHATSAPP_NUMBER": os.getenv("TWILIO_WHATSAPP_NUMBER"),
        "TWITTER_ACCESS_TOKEN": os.getenv("TWITTER_ACCESS_TOKEN"),
        "TWITTER_ACCESS_TOKEN_SECRET": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        "TWITTER_API_KEY": os.getenv("TWITTER_API_KEY"),
        "TWITTER_API_SECRET": os.getenv("TWITTER_API_SECRET"),
        "VAULT_PATH": _resolve_vault_path(os.getenv("VAULT_PATH")),
        "WEBHOOK_PUBLIC_URL": os.getenv("WEBHOOK_PUBLIC_URL"),
        "WEBHOOK_PORT": _int_env("WEBHOOK_PORT", 8001),
        "WHATSAPP_WEBHOOK_VERIFY_TOKEN": os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN"),
    }
