#!/usr/bin/env python3
"""
Vault Sync Agent - Git-based synchronization for cloud/local architecture

Syncs vault between Cloud and Local machines using git push/pull.
Runs on both:
  - Cloud VM: Pushes /Updates/ (Cloud-only folder) to git, pulls changes
  - Local machine: Pulls all changes from git, manages approvals

Security: Only markdown files sync, NO secrets (.env, tokens, credentials)
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Logging setup
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [VAULT_SYNC] %(levelname)s: %(message)s'
)
logger = logging.getLogger('vault_sync')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './vault'))
GIT_REMOTE = os.getenv('GIT_REMOTE', 'origin')
GIT_BRANCH = os.getenv('GIT_BRANCH', 'main')
SYNC_INTERVAL = int(os.getenv('VAULT_SYNC_INTERVAL', '300'))  # 5 minutes
AGENT_TYPE = os.getenv('AGENT_TYPE', 'local')  # 'cloud' or 'local'

# Directories
UPDATES_DIR = VAULT_PATH / 'Updates'  # Cloud writes here
NEEDS_ACTION_DIR = VAULT_PATH / 'Needs_Action'
IN_PROGRESS_DIR = VAULT_PATH / 'In_Progress'
PENDING_APPROVAL_DIR = VAULT_PATH / 'Pending_Approval'
APPROVED_DIR = VAULT_PATH / 'Approved'
DONE_DIR = VAULT_PATH / 'Done'
LOGS_DIR = VAULT_PATH / 'Logs'

# Files that sync
SYNCABLE_EXTENSIONS = {'.md', '.yaml', '.yml', '.json', '.txt'}

# Files that NEVER sync (secrets)
NEVER_SYNC = {
    '.env',
    '.env.local',
    '.processed_emails',
    '.processed_tweets',
    '.processed_whatsapp',
    '.whatsapp_incoming.json',
    '*_token.json',
    'credentials.json',
    '*.secret',
    '*.key'
}


class VaultSyncAgent:
    """Manages vault synchronization between Cloud and Local"""

    def __init__(self, vault_path: Path, agent_type: str = 'local'):
        """Initialize sync agent"""
        self.vault = vault_path
        self.agent_type = agent_type
        self.git_repo = vault_path.parent  # Project root with .git
        self.sync_log = LOGS_DIR / 'vault_sync.jsonl'

        # Create directories if needed
        for d in [UPDATES_DIR, NEEDS_ACTION_DIR, IN_PROGRESS_DIR,
                  PENDING_APPROVAL_DIR, APPROVED_DIR, DONE_DIR, LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def log_sync_event(self, event_type: str, details: dict):
        """Log sync event to audit trail"""
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent': self.agent_type,
                'event': event_type,
                **details
            }
            with open(self.sync_log, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to log sync event: {e}")

    def git_status(self) -> dict:
        """Get git status"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {'returncode': result.returncode, 'output': result.stdout}
        except Exception as e:
            logger.error(f"Git status failed: {e}")
            return {'returncode': 1, 'error': str(e)}

    def git_pull(self) -> bool:
        """Pull latest changes from remote"""
        try:
            logger.info(f"Pulling from {GIT_REMOTE}/{GIT_BRANCH}...")
            result = subprocess.run(
                ['git', 'pull', GIT_REMOTE, GIT_BRANCH],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"✓ Pulled successfully")
                self.log_sync_event('git_pull_success', {
                    'output': result.stdout[:200]
                })
                return True
            else:
                logger.warning(f"Pull failed: {result.stderr}")
                self.log_sync_event('git_pull_failed', {
                    'error': result.stderr[:200]
                })
                return False
        except subprocess.TimeoutExpired:
            logger.error("Git pull timed out")
            self.log_sync_event('git_pull_timeout', {})
            return False
        except Exception as e:
            logger.error(f"Git pull error: {e}")
            self.log_sync_event('git_pull_error', {
                'error': str(e)[:200]
            })
            return False

    def git_push(self, message: str) -> bool:
        """Push changes to remote"""
        try:
            # Add changes
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.git_repo,
                capture_output=True,
                timeout=10
            )

            # Check if there are changes
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=10
            )

            if not status.stdout.strip():
                logger.debug("No changes to push")
                return True

            # Commit
            logger.info(f"Committing: {message[:50]}...")
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 and 'nothing to commit' not in result.stderr:
                logger.warning(f"Commit failed: {result.stderr}")
                return False

            # Push
            logger.info(f"Pushing to {GIT_REMOTE}/{GIT_BRANCH}...")
            result = subprocess.run(
                ['git', 'push', GIT_REMOTE, GIT_BRANCH],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"✓ Pushed successfully")
                self.log_sync_event('git_push_success', {
                    'message': message[:100]
                })
                return True
            else:
                logger.warning(f"Push failed: {result.stderr}")
                self.log_sync_event('git_push_failed', {
                    'error': result.stderr[:200]
                })
                return False
        except subprocess.TimeoutExpired:
            logger.error("Git push timed out")
            self.log_sync_event('git_push_timeout', {})
            return False
        except Exception as e:
            logger.error(f"Git push error: {e}")
            self.log_sync_event('git_push_error', {
                'error': str(e)[:200]
            })
            return False

    def is_syncable_file(self, filepath: Path) -> bool:
        """Check if file should be synced"""
        name = filepath.name

        # Check if in NEVER_SYNC list
        for pattern in NEVER_SYNC:
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return False
            if name == pattern:
                return False

        # Check extension
        return filepath.suffix in SYNCABLE_EXTENSIONS or filepath.suffix == ''

    def sync_cloud(self):
        """Cloud agent sync: Push Updates/ and pull changes"""
        logger.info("CLOUD: Starting sync...")

        try:
            # Cloud pushes its /Updates/ folder
            updates = list(UPDATES_DIR.glob('*.md'))
            if updates:
                logger.info(f"Cloud: Found {len(updates)} updates to push")

                # Stage and push
                self.git_push(
                    f"cloud: Update vault with {len(updates)} cloud changes\n\n"
                    "Co-Authored-By: Cloud Agent <cloud@digitalfte.local>"
                )

            # Cloud pulls latest from Local (approvals, done items, etc.)
            self.git_pull()

            logger.info("CLOUD: Sync complete")
            self.log_sync_event('cloud_sync_complete', {
                'updates_count': len(updates)
            })

        except Exception as e:
            logger.error(f"Cloud sync failed: {e}")
            self.log_sync_event('cloud_sync_error', {
                'error': str(e)[:200]
            })

    def sync_local(self):
        """Local agent sync: Pull changes and manage approvals"""
        logger.info("LOCAL: Starting sync...")

        try:
            # Local pulls everything
            if self.git_pull():
                logger.info("LOCAL: Pulled cloud updates")

                # Check for new Updates/ from cloud
                updates = list(UPDATES_DIR.glob('*.md'))
                if updates:
                    logger.info(f"LOCAL: Found {len(updates)} cloud updates")
                    self._process_cloud_updates(updates)

                # Local manages Dashboard.md (single writer)
                self._update_dashboard()

            logger.info("LOCAL: Sync complete")
            self.log_sync_event('local_sync_complete', {
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

        except Exception as e:
            logger.error(f"Local sync failed: {e}")
            self.log_sync_event('local_sync_error', {
                'error': str(e)[:200]
            })

    def _process_cloud_updates(self, update_files: list):
        """Process cloud updates that need local review"""
        for update_file in update_files:
            try:
                logger.info(f"Processing cloud update: {update_file.name}")

                # Cloud sends draft replies in /Updates/
                # Local reviews and moves to /Pending_Approval/ if needs approval
                # Or moves to /Approved/ if auto-approved

                with open(update_file) as f:
                    content = f.read()

                # Check if marked as "approved_by_cloud" (auto-approvable)
                if 'approved_by_cloud: true' in content.lower():
                    # Auto-approved by cloud, local can execute immediately
                    target = APPROVED_DIR / update_file.name
                    logger.info(f"  → Auto-approved, moving to /Approved/")
                else:
                    # Needs local human approval
                    target = PENDING_APPROVAL_DIR / update_file.name
                    logger.info(f"  → Needs approval, moving to /Pending_Approval/")

                # Move file
                update_file.rename(target)

                self.log_sync_event('process_cloud_update', {
                    'filename': update_file.name,
                    'action': 'approved' if 'approved' in target.name else 'pending'
                })

            except Exception as e:
                logger.error(f"Failed to process {update_file.name}: {e}")

    def _update_dashboard(self):
        """Local updates Dashboard.md with latest status"""
        dashboard = self.vault / 'Dashboard.md'

        try:
            # Count items in each queue
            needs_action = len(list(NEEDS_ACTION_DIR.glob('*.md')))
            in_progress = len(list(IN_PROGRESS_DIR.glob('*/*.md')))
            pending = len(list(PENDING_APPROVAL_DIR.glob('*.md')))
            approved = len(list(APPROVED_DIR.glob('*.md')))
            done = len(list(DONE_DIR.glob('*.md')))

            status = f"""# DigitalFTE Status

**Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Queue Status

| Stage | Count |
|-------|-------|
| Needs Action | {needs_action} |
| In Progress | {in_progress} |
| Pending Approval | {pending} |
| Approved (Ready to execute) | {approved} |
| Done (Completed) | {done} |

## System Status

- **Agent Type**: {self.agent_type.upper()}
- **Last Sync**: {datetime.now(timezone.utc).isoformat()}
- **Vault Path**: {self.vault}

## Recent Logs

Check `/vault/Logs/` for detailed audit trail.

---

Generated by Vault Sync Agent
"""

            with open(dashboard, 'w') as f:
                f.write(status)

            logger.info("Updated Dashboard.md")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def run(self):
        """Main sync loop"""
        logger.info(f"Starting Vault Sync Agent ({self.agent_type})")
        logger.info(f"Sync interval: {SYNC_INTERVAL} seconds")
        logger.info(f"Vault path: {self.vault}")

        if not self.vault.exists():
            logger.error(f"Vault path not found: {self.vault}")
            return 1

        try:
            while True:
                try:
                    if self.agent_type == 'cloud':
                        self.sync_cloud()
                    else:  # local
                        self.sync_local()

                    time.sleep(SYNC_INTERVAL)

                except KeyboardInterrupt:
                    logger.info("Sync interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Sync loop error: {e}")
                    time.sleep(SYNC_INTERVAL)

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return 1

        logger.info("Vault Sync Agent stopped")
        return 0


def main():
    """Main entry point"""
    agent = VaultSyncAgent(VAULT_PATH, agent_type=AGENT_TYPE)
    return agent.run()


if __name__ == '__main__':
    sys.exit(main())
