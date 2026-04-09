#!/usr/bin/env python3
"""Compatibility entrypoint for the main orchestrator."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.orchestrator import start_orchestrator


if __name__ == "__main__":
    start_orchestrator()
