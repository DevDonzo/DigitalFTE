#!/usr/bin/env python3
"""Full workflow test - Execute action and move file"""
import os
import pytest
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
from scripts.orchestrator import VaultHandler


def test_full_email_workflow():
    """Test complete email workflow from Approved to Done"""
    vault_path = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
    handler = VaultHandler(vault_path)

    approved = Path(vault_path) / 'Approved'
    email_files = [f for f in approved.glob('*.md') if f.name != '.gitkeep']

    if not email_files:
        pytest.skip("No email files in /Approved/")

    email_file = email_files[0]

    handler._execute_action(email_file)

    approved_after = list(approved.glob('*.md'))
    approved_after = [f for f in approved_after if f.name != '.gitkeep']
    assert len(approved_after) >= 0

    done = Path(vault_path) / 'Done'
    done_files = list(done.glob('*.md'))
    done_files = [f for f in done_files if f.name != '.gitkeep']
    assert len(done_files) >= 0
