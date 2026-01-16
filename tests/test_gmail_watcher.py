#!/usr/bin/env python3
"""Test Gmail Watcher - Simple test runner"""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).resolve().parents[1]


def test_gmail_watcher_credentials():
    """Test that Gmail credentials exist in environment"""
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        pytest.skip("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET not set in .env")


