#!/usr/bin/env python3
"""Launch the DigitalFTE control center."""

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
        "control_center.server:app",
        host="127.0.0.1",
        port=config["CONTROL_CENTER_PORT"],
        reload=False,
    )
