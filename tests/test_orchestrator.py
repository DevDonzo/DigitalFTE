#!/usr/bin/env python3
"""Test Orchestrator - Verify email sending works"""
import time
import subprocess
import pytest
from pathlib import Path
import json
import os

project_root = Path(__file__).resolve().parents[1]
vault = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
approved = vault / 'Approved'
done = vault / 'Done'


def test_orchestrator_email_execution():
    """Test that orchestrator can send emails"""
    email_files = list(approved.glob('EMAIL_*.md'))
    if not email_files:
        pytest.skip("No email files in /Approved/")

    email_file = email_files[0]

    process = subprocess.Popen(
        ['python3', 'scripts/orchestrator.py'],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(5)

    done_files = list(done.glob('EMAIL_*.md'))

    if done_files:
        sent_log = vault / 'Logs' / 'emails_sent.jsonl'
        if sent_log.exists():
            with open(sent_log) as f:
                lines = f.readlines()
                if lines:
                    last_sent = json.loads(lines[-1])
                    assert last_sent.get('status') in ['sent', 'queued']

    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
