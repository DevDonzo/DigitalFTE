"""Watchdog - Monitors and restarts critical processes"""
import subprocess
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSES = {
    'orchestrator': 'python scripts/orchestrator.py',
    'gmail_watcher': 'python watchers/gmail_watcher.py',
}

def is_process_running(pid_file: Path) -> bool:
    # TODO: Check if process is running
    return False

def check_and_restart():
    for name, cmd in PROCESSES.items():
        logger.info(f'Checking {name}...')
        # TODO: Implement process monitoring
        # TODO: Auto-restart failed processes

while True:
    check_and_restart()
    time.sleep(60)
