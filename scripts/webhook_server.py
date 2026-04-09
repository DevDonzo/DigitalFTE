#!/usr/bin/env python3
"""Compatibility entrypoint for the WhatsApp webhook server."""

import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", "8001"))
    uvicorn.run("agents.webhook_server:app", host="0.0.0.0", port=port, reload=False)
