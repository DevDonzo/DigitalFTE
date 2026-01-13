"""Static tests for MCP server wiring"""
import json
from pathlib import Path


def test_mcp_servers_use_sdk():
    root = Path(__file__).resolve().parents[1]
    # Test that modern MCP servers use SDK
    servers = [
        root / 'mcp_servers' / 'email_mcp' / 'index.js',
        root / 'mcp_servers' / 'browser_mcp' / 'index.js',
        root / 'mcp_servers' / 'meta_social_mcp' / 'index.js',
        root / 'mcp_servers' / 'twitter_mcp' / 'index.js'
    ]

    for server in servers:
        text = server.read_text()
        assert '@anthropic-sdk/mcp-sdk' in text, f"{server.name} missing SDK import"


def test_mcp_config_env_alignment():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'mcp_config.json').read_text())
    envs = {s['name']: s.get('env', {}) for s in config.get('servers', [])}

    assert 'GMAIL_CREDENTIALS_PATH' in envs.get('email', {})
    assert 'XERO_ACCESS_TOKEN' in envs.get('xero', {})
    assert 'XERO_TENANT_ID' in envs.get('xero', {})
