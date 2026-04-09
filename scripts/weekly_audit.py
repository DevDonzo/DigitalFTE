#!/usr/bin/env python3
"""Generate a local weekly briefing from vault activity."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_center.server import ensure_vault_structure, generate_briefing_markdown, get_vault_path


if __name__ == "__main__":
    vault = get_vault_path()
    ensure_vault_structure(vault)
    briefing = generate_briefing_markdown(vault)
    print(f"Generated briefing: {briefing}")
