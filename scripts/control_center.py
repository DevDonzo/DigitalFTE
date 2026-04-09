#!/usr/bin/env python3
"""Launch the DigitalFTE control center."""

import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if __name__ == "__main__":
    port = int(os.getenv("CONTROL_CENTER_PORT", "8282"))
    uvicorn.run("control_center.server:app", host="127.0.0.1", port=port, reload=False)
