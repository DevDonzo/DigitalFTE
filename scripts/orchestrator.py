"""Orchestrator - Real implementation with vault watching & action execution"""
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

class VaultHandler(FileSystemEventHandler):
    def __init__(self, vault_path):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'
        self.approved = self.vault / 'Approved'
        self.pending = self.vault / 'Pending_Approval'
        self.done = self.vault / 'Done'
        
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Handle new inbox items → trigger Claude
        if filepath.parent == self.inbox:
            logger.info(f"📨 Inbox: {filepath.name}")
            self._process_inbox(filepath)
        
        # Handle approved actions → execute
        if filepath.parent == self.approved:
            logger.info(f"✅ Approved: {filepath.name}")
            self._execute_action(filepath)
    
    def _process_inbox(self, filepath):
        """Inbox item detected → Create plan"""
        try:
            plan_file = self.vault / 'Plans' / f"PLAN_{filepath.stem}.md"
            plan_content = f"""---
created: {datetime.now().isoformat()}
status: pending
source: {filepath.name}
---

# Plan: {filepath.stem}

## Analysis
Claude should process: {filepath.name}

## Next Steps
- [ ] Review {filepath.name}
- [ ] Determine if approval needed
- [ ] Create /Pending_Approval/ or execute directly
- [ ] Update this plan

## Notes
Processed at: {datetime.now().isoformat()}
"""
            plan_file.write_text(plan_content)
            logger.info(f"📋 Plan created: {plan_file.name}")
            self._log_action('inbox_processed', filepath.name, 'success')
        except Exception as e:
            logger.error(f"Plan creation error: {e}")
            self._log_action('inbox_error', filepath.name, 'failure', str(e))
    
    def _execute_action(self, filepath):
        """Approved action detected → Execute"""
        try:
            content = filepath.read_text()
            
            # Parse action type from filename
            if 'EMAIL' in filepath.name:
                self._execute_email(filepath, content)
            elif 'PAYMENT' in filepath.name:
                self._execute_payment(filepath, content)
            elif 'POST' in filepath.name:
                self._execute_post(filepath, content)
            else:
                logger.warning(f"Unknown action type: {filepath.name}")
            
            # Move to done
            done_file = self.done / filepath.name
            filepath.rename(done_file)
            logger.info(f"✔️ Done: {done_file.name}")
            self._log_action('action_executed', filepath.name, 'success')
        except Exception as e:
            logger.error(f"Action error: {e}")
            self._log_action('action_error', filepath.name, 'failure', str(e))
    
    def _execute_email(self, filepath, content):
        """Execute email action (would call Email MCP)"""
        logger.info(f"📧 Email action: {filepath.name}")
        # TODO: Call Email MCP server
    
    def _execute_payment(self, filepath, content):
        """Execute payment action (would call Xero MCP)"""
        logger.info(f"💰 Payment action: {filepath.name}")
        # TODO: Call Xero MCP server
    
    def _execute_post(self, filepath, content):
        """Execute social post action (would call Meta/Twitter MCP)"""
        logger.info(f"📱 Post action: {filepath.name}")
        # TODO: Call Meta/Twitter MCP server
    
    def _log_action(self, action_type: str, target: str, result: str, error: str = None):
        """Log to audit trail"""
        try:
            log_file = self.vault / 'Logs' / f"{datetime.now().strftime('%Y-%m-%d')}.json"
            entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'action_type': action_type,
                'actor': 'orchestrator',
                'target': target,
                'result': result,
                'error': error
            }
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Log error: {e}")

def start_orchestrator():
    """Start vault monitoring"""
    vault_path = Path(os.getenv('VAULT_PATH', './vault'))
    
    if not vault_path.exists():
        print(f"ERROR: Vault path {vault_path} doesn't exist")
        exit(1)
    
    handler = VaultHandler(str(vault_path))
    observer = Observer()
    observer.schedule(handler, str(vault_path), recursive=True)
    observer.start()
    
    logger.info(f"🚀 Orchestrator started (watching {vault_path})")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping orchestrator...")
        observer.stop()
    observer.join()

if __name__ == '__main__':
    start_orchestrator()
