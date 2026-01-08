"""Audit Logger - Comprehensive logging for all actions"""
import json
import logging
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action_type: str, target: str = None,
                   parameters: dict = None, result: str = "pending",
                   approval_status: str = None, error: str = None):
        """Log an action to daily audit file"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actor": "claude_code",
            "target": target,
            "parameters": parameters or {},
            "approval_status": approval_status,
            "result": result,
            "error": error
        }

        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{today}.json"

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
