"""Orchestrator - Real implementation with vault watching & action execution"""
import os
import json
import time
import logging
import hashlib
import re
import subprocess
import sys
import base64
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import defaultdict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Import Gmail watcher for marking emails as read
try:
    from watchers.gmail_watcher import GmailWatcher
except ImportError:
    GmailWatcher = None

# Add utils to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.email_drafter import EmailDrafter
    HAS_EMAIL_DRAFTER = True
except ImportError:
    logger.warning("EmailDrafter not available - using legacy email processing")
    HAS_EMAIL_DRAFTER = False

try:
    from utils.tweet_drafter import TweetDrafter
    HAS_TWEET_DRAFTER = True
except ImportError:
    HAS_TWEET_DRAFTER = False

try:
    from utils.whatsapp_drafter import WhatsAppDrafter
    HAS_WHATSAPP_DRAFTER = True
except ImportError:
    HAS_WHATSAPP_DRAFTER = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

class VaultHandler(FileSystemEventHandler):
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    def __init__(self, vault_path):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'  # Legacy, for backwards compatibility
        self.needs_action = self.vault / 'Needs_Action'
        self.approved = self.vault / 'Approved'
        self.pending = self.vault / 'Pending_Approval'
        self.done = self.vault / 'Done'

        # Initialize Gmail service
        self.gmail_service = self._init_gmail_service()

        # Initialize Email Drafter (OpenAI-powered response generation)
        if HAS_EMAIL_DRAFTER:
            self.email_drafter = EmailDrafter(str(vault_path))
            logger.info("✓ Email Drafter initialized (OpenAI-powered)")
        else:
            self.email_drafter = None

        # Initialize Tweet Drafter (OpenAI-powered tweet generation)
        if HAS_TWEET_DRAFTER:
            self.tweet_drafter = TweetDrafter(str(vault_path))
            logger.info("✓ Tweet Drafter initialized (OpenAI-powered)")
        else:
            self.tweet_drafter = None

        # Initialize WhatsApp Drafter (OpenAI-powered response generation)
        if HAS_WHATSAPP_DRAFTER:
            self.whatsapp_drafter = WhatsAppDrafter(str(vault_path))
            logger.info("✓ WhatsApp Drafter initialized (OpenAI-powered)")
        else:
            self.whatsapp_drafter = None

        # Initialize Gmail Watcher for marking emails as read
        self.gmail_watcher = None
        if GmailWatcher:
            try:
                creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
                self.gmail_watcher = GmailWatcher(str(vault_path), creds_path)
                logger.info("✓ Gmail Watcher initialized (for marking emails as read)")
            except Exception as e:
                logger.warning(f"Could not initialize Gmail Watcher: {e}")

        # Batching optimization: buffer events and deduplicate
        self.event_queue = defaultdict(list)
        self.processed_hashes = set()
        self.executed_files = set()  # Track executed files to avoid double processing
        self.last_batch_time = time.time()
        self.batch_timeout = 2.0  # Batch events every 2 seconds

    def _extract_gmail_message_id(self, email_content: str) -> str:
        """Extract gmail_message_id from email file content"""
        lines = email_content.split('\n')
        for line in lines:
            if line.startswith('gmail_message_id:'):
                return line.split(':', 1)[1].strip()
        return None

    def _scan_existing_files(self):
        """Process any existing files in Needs_Action/Approved that were created before startup"""
        logger.info("🔍 Scanning for existing files...")

        # Scan Needs_Action folder for emails needing drafting
        needs_action_files = [f for f in self.needs_action.glob('*.md') if f.name != '.gitkeep']
        if needs_action_files:
            logger.info(f"Found {len(needs_action_files)} existing file(s) in Needs_Action")
            for filepath in needs_action_files:
                try:
                    self._process_inbox(filepath)
                except Exception as e:
                    logger.error(f"Error processing {filepath.name}: {e}")

        # Scan Approved
        approved_files = [f for f in self.approved.glob('*.md') if f.name != '.gitkeep']
        if approved_files:
            logger.info(f"Found {len(approved_files)} existing file(s) in Approved")
            for filepath in approved_files:
                try:
                    self._execute_action(filepath)
                except Exception as e:
                    logger.error(f"Error executing {filepath.name}: {e}")

    def _init_gmail_service(self):
        """Initialize Gmail API service"""
        try:
            creds_path = Path.home() / '.gmail_token.json'
            if not creds_path.exists():
                logger.warning("Gmail token not found - email sending will not work")
                return None

            creds = Credentials.from_authorized_user_file(creds_path, self.SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update token file with refreshed credentials
                with open(creds_path, 'w') as f:
                    f.write(creds.to_json())

            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            return None

    def _get_file_hash(self, filepath):
        """Generate hash of file path for deduplication"""
        return hashlib.md5(str(filepath).encode()).hexdigest()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        file_hash = self._get_file_hash(filepath)

        # Skip if already processed (deduplication)
        if file_hash in self.processed_hashes:
            logger.debug(f"Skipping duplicate event: {filepath.name}")
            return

        self.processed_hashes.add(file_hash)

        # Queue events for batching
        if filepath.parent == self.needs_action:
            self.event_queue['inbox'].append(filepath)  # Keep queue name 'inbox' for backwards compat
            self._process_batch_if_ready('inbox')

        # Handle approved actions → execute
        if filepath.parent == self.approved:
            self.event_queue['approved'].append(filepath)
            self._process_batch_if_ready('approved')

    def _process_batch_if_ready(self, queue_type):
        """Process batch if timeout reached or queue is large enough"""
        queue = self.event_queue[queue_type]
        current_time = time.time()

        # Process if batch is large (50 files) or timeout reached
        if len(queue) >= 50 or (current_time - self.last_batch_time) > self.batch_timeout:
            self._process_batch(queue_type)

    def _process_batch(self, queue_type):
        """Process all files in queue"""
        queue = self.event_queue[queue_type]
        if not queue:
            return

        logger.info(f"Processing batch of {len(queue)} {queue_type} files")
        for filepath in queue:
            try:
                if queue_type == 'inbox':
                    self._process_inbox(filepath)
                elif queue_type == 'approved':
                    self._execute_action(filepath)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")

        self.event_queue[queue_type].clear()
        self.last_batch_time = time.time()
    
    def _process_inbox(self, filepath):
        """Needs_Action item detected → Route to appropriate drafter"""
        try:
            content = filepath.read_text()

            # Check file type based on content or filename
            is_email = 'type: email' in content.lower() or ('from:' in content.lower() and 'type: whatsapp' not in content.lower())
            is_tweet = 'type: tweet' in content.lower() or 'TWEET' in filepath.name.upper() or 'SOCIAL' in filepath.name.upper()
            is_whatsapp = 'type: whatsapp' in content.lower() or 'WHATSAPP' in filepath.name.upper()

            # Route to WhatsApp Drafter
            if is_whatsapp and self.whatsapp_drafter:
                logger.info(f"💬 Using AI to draft WhatsApp reply for: {filepath.name}")
                try:
                    draft_file = self.whatsapp_drafter.draft_reply(filepath)
                    if draft_file:
                        logger.info(f"💬 WhatsApp draft created: {draft_file.name}")
                        self._log_action('whatsapp_draft_created', filepath.name, 'success')
                    else:
                        logger.warning(f"Failed to draft WhatsApp reply for {filepath.name}")
                        self._log_action('whatsapp_draft_failed', filepath.name, 'failure')
                except Exception as e:
                    logger.error(f"Error drafting WhatsApp reply: {e}")
                    self._log_action('whatsapp_draft_error', filepath.name, 'failure', str(e))
                return

            # Route to Tweet Drafter
            if is_tweet and self.tweet_drafter:
                logger.info(f"📱 Using AI to draft tweet for: {filepath.name}")
                try:
                    draft_file = self.tweet_drafter.draft_tweet(filepath)
                    if draft_file:
                        logger.info(f"🐦 Tweet draft created: {draft_file.name}")
                        self._log_action('tweet_draft_created', filepath.name, 'success')
                    else:
                        logger.warning(f"Failed to draft tweet for {filepath.name}")
                        self._log_action('tweet_draft_failed', filepath.name, 'failure')
                except Exception as e:
                    logger.error(f"Error drafting tweet for {filepath.name}: {e}")
                    self._log_action('tweet_draft_error', filepath.name, 'failure', str(e))
                return

            # Route to Email Drafter
            if is_email and self.email_drafter:
                # Use AI Assistant to draft reply
                logger.info(f"🤖 Using AI Assistant to draft reply for: {filepath.name}")
                try:
                    draft_file = self.email_drafter.draft_reply(filepath)

                    if draft_file:
                        logger.info(f"✉️ Draft created: {draft_file.name}")
                        self._log_action('email_draft_created', filepath.name, 'success')

                        # Mark original email as read in Gmail
                        gmail_msg_id = self._extract_gmail_message_id(content)
                        if gmail_msg_id and self.gmail_watcher:
                            self.gmail_watcher.mark_as_read(gmail_msg_id)
                    else:
                        logger.warning(f"Failed to draft reply for {filepath.name}")
                        self._log_action('email_draft_failed', filepath.name, 'failure')
                except Exception as e:
                    logger.error(f"Error drafting reply for {filepath.name}: {e}")
                    self._log_action('email_draft_error', filepath.name, 'failure', str(e))
            else:
                # Legacy: Create generic plan for non-email items
                plan_file = self.vault / 'Plans' / f"PLAN_{filepath.stem}.md"
                plan_content = f"""---
created: {datetime.now().isoformat()}
status: pending
source: {filepath.name}
---

# Plan: {filepath.stem}

## Analysis
AI Assistant should process: {filepath.name}

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
            logger.error(f"Inbox processing error: {e}")
            self._log_action('inbox_error', filepath.name, 'failure', str(e))
    
    def _execute_action(self, filepath):
        """Approved action detected → Execute"""
        # Skip if already executed (deduplication)
        if filepath.name in self.executed_files:
            logger.debug(f"Skipping already-executed file: {filepath.name}")
            return

        try:
            content = filepath.read_text()

            # Mark as executed immediately to prevent double-processing
            self.executed_files.add(filepath.name)

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
        """Execute email action - Send reply via Email MCP"""
        try:
            # Parse YAML frontmatter
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            frontmatter_end = 0

            for i, line in enumerate(lines):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                    else:
                        frontmatter_end = i
                        break
                elif in_frontmatter and ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()

            # Extract reply text - support both formats:
            # 1. New format: ## Proposed Response (from Email Drafter)
            # 2. Legacy format: ## Your Reply
            reply_text = ''
            reply_started = False
            reply_sections = ['## Proposed Response', '## Your Reply']

            for i, line in enumerate(lines[frontmatter_end:]):
                if any(section in line for section in reply_sections):
                    reply_started = True
                    continue
                elif reply_started and line.startswith('##'):
                    break
                elif reply_started:
                    reply_text += line + '\n'

            reply_text = reply_text.strip()

            # Handle both metadata formats
            # Format 1: from (new drafts)
            if 'from' in metadata:
                recipient = metadata.get('from', '').split('<')[-1].rstrip('>')
            # Format 2: original_from (legacy)
            elif 'original_from' in metadata:
                recipient = metadata.get('original_from', '').split('<')[-1].rstrip('>')
            else:
                recipient = None

            subject_base = metadata.get('subject', metadata.get('original_subject', ''))
            subject = 'Re: ' + subject_base if subject_base else 'Re: Message'

            if not reply_text:
                raise ValueError("No reply text found in ## Your Reply section")

            if not recipient:
                raise ValueError(f"No recipient email found in 'from:' field")

            logger.info(f"📧 Sending email to {recipient}")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Body preview: {reply_text[:100]}...")

            # Call Email MCP via Python
            self._call_email_mcp(recipient, subject, reply_text)

            logger.info(f"✉️ Email sent successfully to {recipient}")

        except Exception as e:
            logger.error(f"Email execution failed: {e}")
            raise

    def _call_email_mcp(self, to: str, subject: str, body: str):
        """Send email via Gmail API"""
        if not self.gmail_service:
            raise RuntimeError("Gmail service not initialized - cannot send email")

        try:
            # Create MIME message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}

            result = self.gmail_service.users().messages().send(
                userId='me', body=send_message
            ).execute()

            message_id = result.get('id')
            logger.info(f"✅ Email sent successfully to {to}")
            logger.info(f"   Message ID: {message_id}")

            # Log the sent email
            sent_file = self.vault / 'Logs' / 'emails_sent.jsonl'
            sent_file.parent.mkdir(parents=True, exist_ok=True)

            email_log = {
                'to': to,
                'subject': subject,
                'body': body[:200] + '...' if len(body) > 200 else body,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'sent',
                'message_id': message_id
            }

            with open(sent_file, 'a') as f:
                f.write(json.dumps(email_log) + '\n')

            logger.info(f"📝 Logged to: {sent_file}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def _call_twitter_api(self, text: str, metadata: dict):
        """Post to Twitter/X via API v2 using OAuth 1.0a"""
        import os

        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise RuntimeError("Twitter OAuth credentials not fully configured in .env")

        try:
            from requests_oauthlib import OAuth1Session

            # Create OAuth1 session
            oauth = OAuth1Session(
                api_key,
                client_secret=api_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret,
            )

            # Post tweet
            url = "https://api.twitter.com/2/tweets"
            payload = {"text": text}

            response = oauth.post(url, json=payload)

            if response.status_code != 201:
                error_msg = response.text
                logger.error(f"Twitter API error: {response.status_code} - {error_msg}")
                raise RuntimeError(f"Twitter API error: {response.status_code} - {error_msg}")

            response_data = response.json()
            tweet_id = response_data.get('data', {}).get('id')

            logger.info(f"✅ Tweet posted to Twitter/X")
            logger.info(f"   Tweet ID: {tweet_id}")
            logger.info(f"   URL: https://twitter.com/i/web/status/{tweet_id}")

            # Log the post
            log_file = self.vault / 'Logs' / 'posts_sent.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            post_log = {
                'text': text,
                'platform': 'twitter',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'posted',
                'tweet_id': tweet_id,
                'url': f"https://twitter.com/i/web/status/{tweet_id}"
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(post_log) + '\n')

            logger.info(f"📝 Logged to: {log_file}")

        except ImportError:
            logger.error("requests-oauthlib not installed. Run: pip install requests-oauthlib")
            raise RuntimeError("requests-oauthlib required for Twitter posting")
        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            raise

    def _call_meta_api(self, text: str, metadata: dict):
        """Post to Facebook Page via Graph API"""
        import os
        import requests

        access_token = os.getenv('META_ACCESS_TOKEN')
        page_id = os.getenv('META_PAGE_ID')

        if not access_token:
            raise RuntimeError("META_ACCESS_TOKEN not configured in .env")
        if not page_id:
            raise RuntimeError("META_PAGE_ID not configured in .env")

        try:
            # Post to Facebook Page
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            payload = {
                "message": text,
                "access_token": access_token
            }

            response = requests.post(url, data=payload)

            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Meta API error: {response.status_code} - {error_msg}")
                raise RuntimeError(f"Meta API error: {response.status_code} - {error_msg}")

            response_data = response.json()
            post_id = response_data.get('id')

            logger.info(f"✅ Posted to Facebook")
            logger.info(f"   Post ID: {post_id}")
            logger.info(f"   URL: https://facebook.com/{post_id}")

            # Log the post
            log_file = self.vault / 'Logs' / 'posts_sent.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            post_log = {
                'text': text,
                'platform': 'facebook',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'posted',
                'post_id': post_id,
                'url': f"https://facebook.com/{post_id}"
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(post_log) + '\n')

            logger.info(f"📝 Logged to: {log_file}")

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            raise

    def _execute_payment(self, filepath, content):
        """Execute payment action (would call Xero MCP)"""
        logger.info(f"💰 Payment action: {filepath.name}")
        # TODO: Call Xero MCP server
    
    def _execute_post(self, filepath, content):
        """Execute social post action - Post to Twitter/X or Facebook"""
        try:
            # Parse YAML frontmatter
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            frontmatter_end = 0

            for i, line in enumerate(lines):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                    else:
                        frontmatter_end = i
                        break
                elif in_frontmatter and ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()

            # Determine platform from metadata or filename
            platform = metadata.get('platform', 'twitter').lower()
            if 'facebook' in filepath.name.lower() or 'fb' in filepath.name.lower():
                platform = 'facebook'
            elif 'instagram' in filepath.name.lower() or 'ig' in filepath.name.lower():
                platform = 'instagram'

            # Extract post text - support formats: ## Tweet, ## Post Text, ## Post Content
            post_text = ''
            post_started = False
            post_sections = ['## Tweet', '## Post Text', '## Post Content', '## Facebook Post']

            for i, line in enumerate(lines[frontmatter_end:]):
                if any(section in line for section in post_sections):
                    post_started = True
                    continue
                elif post_started and line.startswith('##'):
                    break
                elif post_started:
                    post_text += line + '\n'

            post_text = post_text.strip()

            if not post_text:
                raise ValueError("No post text found")

            # Route to appropriate platform
            if platform == 'twitter':
                if len(post_text) > 280:
                    logger.warning(f"Tweet exceeds 280 chars ({len(post_text)}), truncating")
                    post_text = post_text[:277] + "..."

                logger.info(f"📱 Posting to Twitter/X")
                logger.info(f"   Text: {post_text}")
                self._call_twitter_api(post_text, metadata)
                logger.info(f"✅ Tweet posted successfully")

            elif platform in ['facebook', 'fb']:
                logger.info(f"📘 Posting to Facebook")
                logger.info(f"   Text: {post_text}")
                self._call_meta_api(post_text, metadata)
                logger.info(f"✅ Facebook post successful")

            elif platform in ['instagram', 'ig']:
                logger.warning(f"Instagram requires image - skipping text-only post")
                raise ValueError("Instagram requires an image URL")

            else:
                logger.warning(f"Unknown platform: {platform}, defaulting to Twitter")
                self._call_twitter_api(post_text, metadata)

        except Exception as e:
            logger.error(f"Post execution failed: {e}")
            raise
    
    def _log_action(self, action_type: str, target: str, result: str, error: str = None):
        """Log to audit trail"""
        try:
            log_file = self.vault / 'Logs' / f"{datetime.now().strftime('%Y-%m-%d')}.json"
            entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
    """Start vault monitoring with batching optimization"""
    vault_path = Path(os.getenv('VAULT_PATH', './vault'))

    if not vault_path.exists():
        print(f"ERROR: Vault path {vault_path} doesn't exist")
        exit(1)

    handler = VaultHandler(str(vault_path))
    observer = Observer()
    observer.schedule(handler, str(vault_path), recursive=True)
    observer.start()

    # Process any existing files before watching for new ones
    handler._scan_existing_files()

    logger.info(f"🚀 Orchestrator started (watching {vault_path})")
    logger.info("📦 Batching enabled: processes events in batches every 2s or when 50+ events queue")

    # Track last approved folder scan
    last_approved_scan = time.time()
    approved_scan_interval = 5  # Scan every 5 seconds

    try:
        while True:
            # Periodically flush batches to ensure timely processing
            current_time = time.time()
            if (current_time - handler.last_batch_time) > handler.batch_timeout:
                for queue_type in ['inbox', 'approved']:
                    if handler.event_queue[queue_type]:
                        handler._process_batch(queue_type)

            # Periodically scan Approved folder for any files that weren't caught by watchdog
            if (current_time - last_approved_scan) > approved_scan_interval:
                approved_files = [f for f in handler.approved.glob('*.md') if f.name != '.gitkeep']
                for filepath in approved_files:
                    try:
                        handler._execute_action(filepath)
                    except Exception as e:
                        logger.error(f"Error executing {filepath.name}: {e}")
                last_approved_scan = current_time

            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Stopping orchestrator...")
        # Flush any remaining batches
        for queue_type in ['inbox', 'approved']:
            if handler.event_queue[queue_type]:
                handler._process_batch(queue_type)
        observer.stop()
    observer.join()

if __name__ == '__main__':
    start_orchestrator()
