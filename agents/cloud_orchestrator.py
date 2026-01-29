#!/usr/bin/env python3
"""
Cloud Orchestrator - Always-On Agent

Runs on Oracle Cloud VM 24/7:
- Monitors: Email (Gmail), Social (Twitter, LinkedIn)
- Generates: Draft replies & posts (via AI)
- Outputs: /Updates/ folder (synced to local via git)
- Policy: DRAFT-ONLY (no sending, no posting)

Security: Only cloud secrets in .env (no WhatsApp, Banking, Payment)
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [CLOUD] %(levelname)s: %(message)s'
)
logger = logging.getLogger('cloud_orchestrator')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './vault'))
AGENT_TYPE = os.getenv('AGENT_TYPE', 'cloud')
WATCHERS_ENABLED = os.getenv('CLOUD_WATCHERS', 'gmail,twitter,linkedin').split(',')
WATCHER_CHECK_INTERVAL = int(os.getenv('WATCHER_CHECK_INTERVAL', '120'))  # 2 minutes

# Directories
UPDATES_DIR = VAULT_PATH / 'Updates'
NEEDS_ACTION_DIR = VAULT_PATH / 'Needs_Action'
PLANS_DIR = VAULT_PATH / 'Plans'
LOGS_DIR = VAULT_PATH / 'Logs'


class CloudOrchestrator:
    """Cloud-side orchestrator for draft generation and watchers"""

    def __init__(self):
        """Initialize cloud orchestrator"""
        self.vault = VAULT_PATH
        self.agent_type = AGENT_TYPE

        # Create directories
        for d in [UPDATES_DIR, NEEDS_ACTION_DIR, PLANS_DIR, LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        # Try to import watchers
        self.gmail_watcher = self._import_watcher('gmail_watcher', 'GmailWatcher')
        self.twitter_watcher = self._import_watcher('twitter_watcher', 'TwitterWatcher')
        self.linkedin_watcher = self._import_watcher('linkedin_watcher', 'LinkedInWatcher')

        # Try to import email drafter
        try:
            from utils.email_drafter import EmailDrafter
            self.email_drafter = EmailDrafter()
            logger.info("✓ Email drafter available")
        except ImportError:
            logger.warning("Email drafter not available")
            self.email_drafter = None

        logger.info(f"Cloud Orchestrator initialized (Agent: {AGENT_TYPE})")

    def _import_watcher(self, module_name: str, class_name: str):
        """Safely import watcher"""
        try:
            if module_name == 'gmail_watcher':
                from agents.gmail_watcher import GmailWatcher
                return GmailWatcher()
            elif module_name == 'twitter_watcher':
                from agents.twitter_watcher import TwitterWatcher
                return TwitterWatcher()
            elif module_name == 'linkedin_watcher':
                from agents.linkedin_watcher import LinkedInWatcher
                return LinkedInWatcher()
        except ImportError:
            logger.debug(f"{class_name} not available")
            return None

    def log_event(self, event_type: str, details: dict):
        """Log cloud event to audit trail"""
        try:
            event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent': 'cloud',
                'event': event_type,
                **details
            }
            log_file = LOGS_DIR / f"cloud_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def check_gmail_watcher(self):
        """Check for new emails and draft replies"""
        if 'gmail' not in WATCHERS_ENABLED or not self.gmail_watcher:
            return 0

        try:
            logger.info("Checking Gmail for new messages...")

            # Get new emails
            emails = self.gmail_watcher.check_for_updates()
            if not emails:
                logger.debug("No new emails")
                return 0

            processed = 0
            for email in emails:
                try:
                    # Extract email details
                    sender = email.get('from', 'unknown')
                    subject = email.get('subject', '(no subject)')
                    body = email.get('body', '')
                    message_id = email.get('gmail_message_id', '')

                    logger.info(f"Processing email from {sender}: {subject[:50]}")

                    # Draft reply using AI
                    if self.email_drafter:
                        try:
                            reply_draft = self.email_drafter.draft_reply(
                                sender=sender,
                                subject=subject,
                                body=body,
                                context={'source': 'cloud_watcher'}
                            )
                        except Exception as e:
                            logger.warning(f"Failed to draft reply: {e}")
                            reply_draft = "[Could not generate reply - manual review needed]"
                    else:
                        reply_draft = "[Cloud drafter not configured - manual review needed]"

                    # Create draft output in /Updates/
                    draft_name = f"EMAIL_DRAFT_{int(time.time())}.md"
                    draft_file = UPDATES_DIR / draft_name

                    draft_content = f"""---
action: email_reply
from: {sender}
subject: Re: {subject}
message_id: {message_id}
status: draft
timestamp: {datetime.now(timezone.utc).isoformat()}
---

## Original Email

**From**: {sender}
**Subject**: {subject}
**Date**: {datetime.now().isoformat()}

{body}

---

## Suggested Reply

{reply_draft}

---

## Status

This email reply has been drafted by Cloud Agent and is awaiting Local approval.

Move to `/Approved/` to send via local Gmail, or `/Rejected/` to discard.
"""

                    with open(draft_file, 'w') as f:
                        f.write(draft_content)

                    logger.info(f"✓ Draft created: {draft_name}")
                    self.log_event('email_draft_created', {
                        'filename': draft_name,
                        'from': sender,
                        'subject': subject[:50]
                    })

                    processed += 1

                except Exception as e:
                    logger.error(f"Failed to process email from {sender}: {e}")
                    self.log_event('email_processing_error', {
                        'error': str(e)[:200]
                    })

            logger.info(f"Gmail check complete: {processed} drafts created")
            return processed

        except Exception as e:
            logger.error(f"Gmail watcher error: {e}")
            self.log_event('gmail_check_error', {
                'error': str(e)[:200]
            })
            return 0

    def check_twitter_watcher(self):
        """Check for Twitter mentions and draft responses"""
        if 'twitter' not in WATCHERS_ENABLED or not self.twitter_watcher:
            return 0

        try:
            logger.info("Checking Twitter for new mentions...")

            # Get new mentions (to be implemented in twitter_watcher)
            mentions = self.twitter_watcher.check_for_updates()
            if not mentions:
                logger.debug("No new Twitter mentions")
                return 0

            processed = 0
            for mention in mentions:
                try:
                    author = mention.get('author', 'unknown')
                    text = mention.get('text', '')
                    tweet_id = mention.get('id', '')

                    logger.info(f"Processing tweet from {author}")

                    # Draft response (placeholder)
                    response_draft = f"Thank you @{author} for your message. [AI-generated response pending]"

                    # Create draft output
                    draft_name = f"TWEET_DRAFT_{int(time.time())}.md"
                    draft_file = UPDATES_DIR / draft_name

                    draft_content = f"""---
action: twitter_reply
author: {author}
tweet_id: {tweet_id}
status: draft
timestamp: {datetime.now(timezone.utc).isoformat()}
---

## Original Tweet

**From**: @{author}

{text}

---

## Suggested Response

{response_draft}

---

## Status

This tweet response has been drafted by Cloud Agent and is awaiting Local approval.
"""

                    with open(draft_file, 'w') as f:
                        f.write(draft_content)

                    logger.info(f"✓ Draft created: {draft_name}")
                    self.log_event('tweet_draft_created', {
                        'filename': draft_name,
                        'author': author
                    })

                    processed += 1

                except Exception as e:
                    logger.error(f"Failed to process tweet: {e}")

            return processed

        except Exception as e:
            logger.error(f"Twitter watcher error: {e}")
            self.log_event('twitter_check_error', {
                'error': str(e)[:200]
            })
            return 0

    def check_linkedin_watcher(self):
        """Check for LinkedIn activity and draft responses"""
        if 'linkedin' not in WATCHERS_ENABLED or not self.linkedin_watcher:
            return 0

        try:
            logger.info("Checking LinkedIn for new activity...")

            # Get new activity (to be implemented)
            activities = self.linkedin_watcher.check_for_updates()
            if not activities:
                logger.debug("No new LinkedIn activity")
                return 0

            processed = 0
            for activity in activities:
                # Process LinkedIn activity (similar pattern to Twitter)
                processed += 1

            return processed

        except Exception as e:
            logger.error(f"LinkedIn watcher error: {e}")
            self.log_event('linkedin_check_error', {
                'error': str(e)[:200]
            })
            return 0

    def run_watchers_cycle(self):
        """Run one cycle of all watchers"""
        total_drafts = 0

        try:
            logger.info("=" * 60)
            logger.info("Starting watchers cycle")

            total_drafts += self.check_gmail_watcher()
            total_drafts += self.check_twitter_watcher()
            total_drafts += self.check_linkedin_watcher()

            logger.info(f"Watchers cycle complete: {total_drafts} total drafts")
            self.log_event('watchers_cycle_complete', {
                'total_drafts': total_drafts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

        except Exception as e:
            logger.error(f"Watchers cycle error: {e}")
            self.log_event('watchers_cycle_error', {
                'error': str(e)[:200]
            })

        return total_drafts

    def run(self):
        """Main run loop"""
        logger.info(f"Cloud Orchestrator starting (Agent: {AGENT_TYPE})")
        logger.info(f"Watchers: {', '.join(WATCHERS_ENABLED)}")
        logger.info(f"Check interval: {WATCHER_CHECK_INTERVAL} seconds")

        if self.agent_type != 'cloud':
            logger.error(f"ERROR: AGENT_TYPE must be 'cloud', got '{self.agent_type}'")
            return 1

        try:
            while True:
                try:
                    # Run watchers
                    self.run_watchers_cycle()

                    # Wait before next cycle
                    time.sleep(WATCHER_CHECK_INTERVAL)

                except KeyboardInterrupt:
                    logger.info("Cloud orchestrator interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
                    time.sleep(WATCHER_CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return 1

        logger.info("Cloud Orchestrator stopped")
        return 0


def main():
    """Main entry point"""
    orchestrator = CloudOrchestrator()
    return orchestrator.run()


if __name__ == '__main__':
    sys.exit(main())
