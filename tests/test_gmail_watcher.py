#!/usr/bin/env python3
"""Test Gmail Watcher - Simple test runner"""
import pytest
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
from watchers.gmail_watcher import GmailWatcher


def test_gmail_watcher_credentials():
    """Test that Gmail credentials exist"""
    creds_path = str(project_root / 'credentials.json')
    if not Path(creds_path).exists():
        pytest.skip(f"Credentials not found at {creds_path}")

