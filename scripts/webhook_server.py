#!/usr/bin/env python3
"""Compatibility entrypoint for the WhatsApp webhook server."""

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.config_loader import load_config


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "agents.webhook_server:app",
        host="0.0.0.0",
        port=config["WEBHOOK_PORT"],
        reload=False,
    )
