"""Static tests for the active adapter wiring."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_mcp_prototypes_are_not_registered():
    """Do not advertise prototypes that depend on a nonexistent SDK package."""
    config = json.loads((ROOT / "config" / "mcp_config.json").read_text(encoding="utf-8"))

    assert config == {"servers": []}


def test_odoo_adapter_has_supported_runtime_wiring():
    package = json.loads(
        (ROOT / "mcp_servers" / "odoo_mcp" / "package.json").read_text(encoding="utf-8")
    )
    orchestrator = (ROOT / "agents" / "orchestrator.py").read_text(encoding="utf-8")

    assert {"axios", "dotenv"} <= set(package["dependencies"])
    assert "mcp_servers' / 'odoo_mcp' / 'index.js" in orchestrator
    assert "'--legacy-stdio'" in orchestrator
