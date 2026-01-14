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
import threading
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Avoid local scripts/watchdog.py shadowing watchdog package when running as script.
scripts_dir = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == scripts_dir:
    sys.path.pop(0)

from watchdog.observers import Observer as _Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

Observer = PollingObserver if os.getenv("WATCHDOG_USE_POLLING") == "1" else _Observer

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

try:
    from utils.social_post_drafter import SocialPostDrafter
    HAS_SOCIAL_DRAFTER = True
except ImportError:
    HAS_SOCIAL_DRAFTER = False

try:
    from watchers.whatsapp_watcher import WhatsAppWatcher as WhatsAppBusinessAPI
    HAS_WHATSAPP_API = True
except ImportError:
    HAS_WHATSAPP_API = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Log import status
if HAS_EMAIL_DRAFTER:
    logger.info("✓ EmailDrafter available")
else:
    logger.warning("EmailDrafter not available - using legacy email processing")

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

        # Initialize Social Post Drafter (OpenAI-powered multi-platform posts)
        if HAS_SOCIAL_DRAFTER:
            self.social_drafter = SocialPostDrafter(str(vault_path))
            logger.info("✓ Social Post Drafter initialized (OpenAI-powered)")
        else:
            self.social_drafter = None

        # Initialize WhatsApp Business API for sending messages
        self.whatsapp_api = None
        if HAS_WHATSAPP_API:
            try:
                self.whatsapp_api = WhatsAppBusinessAPI(str(vault_path))
                logger.info("✓ WhatsApp Business API initialized")
            except Exception as e:
                logger.warning(f"Could not initialize WhatsApp Business API: {e}")

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
        self.invoice_drafts_created = set()  # Track (source_file, message_id) pairs to prevent duplication
        self.recently_processed_files = {}  # Track (filename: timestamp) to prevent duplicate drafting
        self.dedup_window = 5.0  # Prevent reprocessing same file within 5 seconds
        self.last_batch_time = time.time()
        self.batch_timeout = 2.0  # Batch events every 2 seconds

        # Lock for thread-safe deduplication (prevents race conditions when multiple events fire simultaneously)
        self.dedup_lock = threading.Lock()

        # Refresh Xero token at startup (30-min expiry)
        self._refresh_xero_token_if_needed()

    def _refresh_xero_token_if_needed(self):
        """Refresh Xero OAuth token if expired or expiring soon"""
        try:
            import json
            import time as time_module
            
            token_file = os.path.expanduser('~/.xero_token.json')
            if not os.path.exists(token_file):
                logger.debug("Xero token file not found - skipping refresh")
                return
            
            with open(token_file) as f:
                tokens = json.load(f)
            
            # Check if token is expired or expiring within 5 minutes
            access_token = tokens.get('access_token', '')
            if not access_token:
                return
            
            # Decode JWT to check expiration
            try:
                parts = access_token.split('.')
                if len(parts) != 3:
                    return
                
                payload = parts[1] + '==' * (4 - len(parts[1]) % 4)
                decoded = json.loads(__import__('base64').urlsafe_b64decode(payload))
                exp_time = decoded.get('exp', 0)
                current_time = time_module.time()
                
                # Refresh if expired or expiring within 5 minutes (300 sec)
                if current_time > exp_time - 300:
                    logger.info("🔄 Xero token expiring soon - refreshing...")
                    self._call_xero_refresh_token()
            except Exception as e:
                logger.debug(f"Could not check token expiration: {e}")
        except Exception as e:
            logger.warning(f"Xero token refresh check failed: {e}")
    
    def _call_xero_refresh_token(self):
        """Refresh Xero token via auth script"""
        try:
            auth_script = Path(__file__).parent.parent / 'auth' / 'xero.py'
            result = subprocess.run(
                [sys.executable, str(auth_script), 'refresh'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ Xero token refreshed successfully")
                
                # Update .env with new token
                import json
                token_file = os.path.expanduser('~/.xero_token.json')
                with open(token_file) as f:
                    tokens = json.load(f)
                
                new_token = tokens.get('access_token', '')
                if new_token:
                    # Update .env
                    env_path = Path(__file__).parent.parent / '.env'
                    if env_path.exists():
                        with open(env_path) as f:
                            env_content = f.read()
                        
                        # Replace token using regex
                        import re
                        env_content = re.sub(
                            r'XERO_ACCESS_TOKEN=.*',
                            f'XERO_ACCESS_TOKEN={new_token}',
                            env_content
                        )
                        
                        with open(env_path, 'w') as f:
                            f.write(env_content)
                        
                        # Reload environment
                        os.environ['XERO_ACCESS_TOKEN'] = new_token
                        logger.info("✅ .env updated with fresh Xero token")
            else:
                logger.warning(f"Xero token refresh failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Xero token refresh timed out")
        except Exception as e:
            logger.warning(f"Failed to refresh Xero token: {e}")

    def _extract_gmail_message_id(self, email_content: str) -> str:
        """Extract gmail_message_id from email file content"""
        lines = email_content.split('\n')
        for line in lines:
            if line.startswith('gmail_message_id:'):
                return line.split(':', 1)[1].strip()
        return None

    def _is_post_request(self, email_content: str) -> bool:
        """Check if email is requesting a social media post"""
        content_lower = email_content.lower()
        post_keywords = [
            'post to', 'post about', 'post this', 'tweet about', 'tweet this',
            'share on', 'share to', 'social media', 'facebook', 'linkedin',
            'twitter', 'please post', 'can you post', 'pls post'
        ]
        return any(keyword in content_lower for keyword in post_keywords)

    def _extract_post_request(self, email_content: str) -> tuple:
        """Extract topic and context from post request email. Returns (topic, context)"""
        content_lower = email_content.lower()

        # Find the content after "## Body" section
        body_section = email_content.split('## Body')[-1] if '## Body' in email_content else email_content

        # Extract topic from "post about X" or "post about:"
        lines = body_section.split('\n')
        topic = None
        context = body_section.strip()

        for line in lines:
            if any(keyword in line.lower() for keyword in ['post about', 'post to', 'tweet about', 'share']):
                # Extract the topic from this line
                parts = line.split(':', 1)
                if len(parts) > 1:
                    topic = parts[1].strip()
                    break
                else:
                    # Try to get the next meaningful part
                    words = line.split()
                    idx = -1
                    for i, word in enumerate(words):
                        if word.lower() in ['about', 'to', 'this']:
                            idx = i + 1
                            break
                    if idx > 0 and idx < len(words):
                        topic = ' '.join(words[idx:])
                        break

        # If no explicit topic found, use the whole body
        if not topic:
            topic = body_section.strip()[:200]  # First 200 chars

        return topic, context

    def _scan_existing_files(self):
        """Process any existing files in Inbox/Needs_Action/Approved that were created before startup"""
        logger.info("🔍 Scanning for existing files...")

        # Scan Inbox folder (legacy location)
        inbox_files = [f for f in self.inbox.glob('*.md') if f.name != '.gitkeep']
        if inbox_files:
            logger.info(f"Found {len(inbox_files)} existing file(s) in Inbox")
            for filepath in inbox_files:
                try:
                    # Mark as processed before processing to prevent watcher events from re-processing
                    self.processed_hashes.add(filepath.name)
                    self._process_inbox(filepath)
                except Exception as e:
                    logger.error(f"Error processing {filepath.name}: {e}")

        # Scan Needs_Action folder for emails needing drafting
        needs_action_files = [f for f in self.needs_action.glob('*.md') if f.name != '.gitkeep']
        if needs_action_files:
            logger.info(f"Found {len(needs_action_files)} existing file(s) in Needs_Action")
            for filepath in needs_action_files:
                try:
                    # Mark as processed before processing to prevent watcher events from re-processing
                    self.processed_hashes.add(filepath.name)
                    self._process_inbox(filepath)
                except Exception as e:
                    logger.error(f"Error processing {filepath.name}: {e}")

        # Scan Approved
        approved_files = [f for f in self.approved.glob('*.md') if f.name != '.gitkeep']
        if approved_files:
            logger.info(f"Found {len(approved_files)} existing file(s) in Approved")
            for filepath in approved_files:
                try:
                    # Mark as executed before executing to prevent watcher events from re-executing
                    self.executed_files.add(filepath.name)
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

        # Queue events for batching
        if filepath.parent == self.needs_action:
            # Thread-safe deduplication using lock
            with self.dedup_lock:
                # Skip if already processed
                if filepath.name in self.processed_hashes:
                    logger.debug(f"Skipping already-processed file: {filepath.name}")
                    return

                # Mark as processed immediately to prevent ANY re-processing
                self.processed_hashes.add(filepath.name)

            # Queue outside lock to avoid holding it during batch processing
            self.event_queue['inbox'].append(filepath)
            self._process_batch_if_ready('inbox')

        # Handle approved actions → execute
        elif filepath.parent == self.approved:
            # Thread-safe deduplication using lock
            with self.dedup_lock:
                # Skip if already executed
                if filepath.name in self.executed_files:
                    logger.debug(f"Skipping already-executed file: {filepath.name}")
                    return

                # Mark as executed immediately to prevent ANY re-execution
                self.executed_files.add(filepath.name)

            # Queue outside lock to avoid holding it during batch processing
            # But don't process the batch here - let the queue handler do it
            # to avoid double-execution if the batch is already being processed
            self.event_queue['approved'].append(filepath)
            self._process_batch_if_ready('approved')

    def on_modified(self, event):
        """Handle file modifications - same deduplication as on_created"""
        # Treat modified events the same as created events (prevent re-processing)
        # This handles watchdog firing multiple events when files are written
        if event.is_directory:
            return

        # For Needs_Action and Approved folders, modified events should be ignored
        # since we already process on_created and use deduplication
        logger.debug(f"Ignoring modified event for: {Path(event.src_path).name}")

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

        # Deduplicate: remove duplicate filenames from queue (file system watchers can fire multiple events)
        seen_names = set()
        unique_queue = []
        for filepath in queue:
            if filepath.name not in seen_names:
                seen_names.add(filepath.name)
                unique_queue.append(filepath)
            else:
                logger.debug(f"Removing duplicate from queue: {filepath.name}")

        # For approved files, also skip if already executed
        if queue_type == 'approved':
            filtered_queue = []
            for filepath in unique_queue:
                if filepath.name in self.executed_files:
                    logger.debug(f"Batch: Skipping already-executed file: {filepath.name}")
                else:
                    filtered_queue.append(filepath)
            unique_queue = filtered_queue

        logger.info(f"Processing batch of {len(unique_queue)} {queue_type} files")
        for filepath in unique_queue:
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
            # Deduplication: Skip if file was recently processed (within dedup_window)
            with self.dedup_lock:
                current_time = time.time()
                if filepath.name in self.recently_processed_files:
                    last_processed = self.recently_processed_files[filepath.name]
                    if current_time - last_processed < self.dedup_window:
                        logger.debug(f"⏭️ Skipping recently processed file: {filepath.name}")
                        return

                # Clean up old entries (older than 30 seconds)
                self.recently_processed_files = {
                    fname: ftime for fname, ftime in self.recently_processed_files.items()
                    if current_time - ftime < 30.0
                }

                # Mark this file as processed now
                self.recently_processed_files[filepath.name] = current_time

            content = filepath.read_text()

            # Check file type based on content or filename
            is_email = 'type: email' in content.lower() or ('from:' in content.lower() and 'type: whatsapp' not in content.lower())
            is_tweet = 'type: tweet' in content.lower() or 'TWEET' in filepath.name.upper() or 'SOCIAL' in filepath.name.upper()
            is_whatsapp = 'type: whatsapp' in content.lower() or 'WHATSAPP' in filepath.name.upper()

            # Route to WhatsApp Drafter
            if is_whatsapp and self.whatsapp_drafter:
                logger.info(f"💬 Using AI to draft WhatsApp reply for: {filepath.name}")
                # NOTE: Do NOT auto-create invoice drafts for WhatsApp messages
                # Let user manually request invoice if needed by moving draft to Approved
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
                self._maybe_create_invoice_draft(filepath, content, channel='email')
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

                # Check if email is requesting a social media post
                if self.social_drafter and self._is_post_request(content):
                    logger.info(f"📱 Detected social media post request in: {filepath.name}")
                    try:
                        topic, context = self._extract_post_request(content)
                        if topic:
                            posts = self.social_drafter.draft_posts(topic, context)
                            if posts:
                                logger.info(f"📱 Generated {len(posts)} social media drafts")
                                for platform, draft_path in posts.items():
                                    logger.info(f"   ✓ {platform.title()}: {draft_path.name}")
                                self._log_action('social_drafts_created', filepath.name, 'success', json.dumps(list(posts.keys())))
                            else:
                                logger.warning(f"Failed to generate social media drafts for {filepath.name}")
                                self._log_action('social_drafts_failed', filepath.name, 'failure')
                    except Exception as e:
                        logger.error(f"Error generating social posts: {e}")
                        self._log_action('social_drafts_error', filepath.name, 'failure', str(e))
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

    def _maybe_create_invoice_draft(self, filepath, content, channel):
        """Create an invoice draft when an incoming message requests an invoice."""
        if not self._is_invoice_request(content):
            return
        message_id = self._extract_message_id(content)

        # Check if we've already created an invoice draft for this message in this run
        dedupe_key = (filepath.name, message_id or '')
        if dedupe_key in self.invoice_drafts_created:
            logger.debug(f"🧾 Invoice draft already created this run for {filepath.name}; skipping")
            return

        # Also check filesystem to avoid recreating drafts from previous runs
        if self._invoice_draft_exists(filepath.name, message_id=message_id):
            logger.info(f"🧾 Invoice draft already exists for {filepath.name}; skipping")
            return

        try:
            contact_name = self._extract_contact_name(content, fallback=filepath.stem)
            amount = self._extract_amount(content)
            due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            description = f"Invoice requested via {channel}"

            draft_name = f"INVOICE_DRAFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            draft_path = self.vault / 'Pending_Approval' / draft_name
            draft_path.parent.mkdir(parents=True, exist_ok=True)

            draft_content = f"""---
type: invoice_draft
source_file: {filepath.name}
message_id: {message_id or ''}
contact_name: {contact_name}
amount: {amount:.2f}
description: {description}
due_date: {due_date}
status: pending_approval
---

## Invoice Draft

- Contact: {contact_name}
- Amount: {amount:.2f}
- Description: {description}
- Due Date: {due_date}

## Actions

- [ ] Review and edit invoice details above if needed
- [ ] Move to /Approved/ to create the invoice in Xero
- [ ] Delete to discard
"""

            draft_path.write_text(draft_content)
            self.invoice_drafts_created.add(dedupe_key)
            logger.info(f"🧾 Invoice draft created: {draft_path.name} (amount: ${amount:.2f})")
            self._log_action('invoice_draft_created', filepath.name, 'success', draft_path.name)
        except Exception as e:
            logger.error(f"Failed to create invoice draft for {filepath.name}: {e}")
            self._log_action('invoice_draft_error', filepath.name, 'failure', str(e))

    def _invoice_draft_exists(self, source_filename, message_id=None):
        drafts_dir = self.vault / 'Pending_Approval'
        if not drafts_dir.exists():
            return False
        for draft in drafts_dir.glob('INVOICE_DRAFT_*.md'):
            try:
                text = draft.read_text()
            except Exception:
                continue
            if f"source_file: {source_filename}" in text:
                return True
            if message_id and f"message_id: {message_id}" in text:
                return True
        return False

    def _is_invoice_request(self, content):
        return 'invoice' in content.lower()

    def _extract_amount(self, content):
        """Extract invoice amount from message content. Prefer body over metadata."""
        lines = content.splitlines()
        body_lines = []

        # Find the message content section (skip frontmatter & metadata)
        in_frontmatter = True
        for i, line in enumerate(lines):
            lowered = line.strip().lower()

            # Exit frontmatter at closing ---
            if in_frontmatter and line.strip() == '---' and i > 0:
                in_frontmatter = False
                continue

            if in_frontmatter:
                continue

            # Look for content section markers
            if (
                lowered == '## message content'
                or lowered == '## content'
                or lowered == '## whatsapp message'
                or lowered == '## email body'
            ):
                # Found content section, extract remaining lines
                body_lines = lines[i + 1 :]
                break

        # If no content section found, use all non-frontmatter lines
        if not body_lines:
            body_lines = [l for l in lines if not l.strip().startswith('---') and l.strip()]

        # Filter out metadata lines
        filtered = []
        for line in body_lines:
            lower = line.strip().lower()
            # Skip metadata rows and markdown section headers
            if (
                lower.startswith(('from:', 'to:', 'created:', 'date:', 'message_id:', 'contact:'))
                or lower.startswith('#')
                or lower == ''
            ):
                continue
            filtered.append(line)

        body = "\n".join(filtered)

        def parse_amounts(matches):
            """Convert matched strings to floats, handling commas."""
            values = []
            for match in matches:
                normalized = match.replace(',', '')
                try:
                    val = float(normalized)
                    # Only accept reasonable amounts ($10 to $1M)
                    if 10 <= val <= 1000000:
                        values.append(val)
                except ValueError:
                    continue
            return values

        # Try currency format first: $1000, $1,000, $1,000.00
        # Pattern: $ followed by digits with optional commas and decimals
        matches = re.findall(
            r'\$\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',
            body
        )
        values = parse_amounts(matches)
        if values:
            return max(values)

        # Fallback: plain numbers like 1000 or 1,000 (excluding timestamps/IDs)
        matches = re.findall(
            r'\b([0-9]{4,}(?:\.[0-9]{1,2})?)\b',  # Only 4+ digit numbers to avoid IDs
            body
        )
        values = parse_amounts(matches)
        if values:
            return max(values)

        # Last resort: $100-$999 without commas
        matches = re.findall(
            r'\$\s*([0-9]{2,3}(?:\.[0-9]{1,2})?)',
            body
        )
        values = parse_amounts(matches)
        if values:
            return max(values)

        logger.warning(f"No valid amount found in message, defaulting to $100.00")
        return 100.00

    def _extract_message_id(self, content):
        for line in content.splitlines():
            if line.lower().startswith('message_id:'):
                return line.split(':', 1)[1].strip()
            if line.lower().startswith('**message id**'):
                return line.split(':', 1)[1].strip()
        return None

    def _extract_contact_name(self, content, fallback):
        for line in content.splitlines():
            if line.lower().startswith('from:'):
                value = line.split(':', 1)[1].strip()
                if '<' in value:
                    return value.split('<', 1)[0].strip() or fallback
                return value or fallback
        return fallback
    
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

            # Extract urgency and priority from frontmatter
            urgency = 'NORMAL'
            priority = 'NORMAL'
            if content.startswith('---'):
                frontmatter_end = content.find('---', 3)
                if frontmatter_end > 0:
                    frontmatter = content[:frontmatter_end]
                    for line in frontmatter.split('\n'):
                        if line.startswith('urgency:'):
                            urgency = line.split(':', 1)[1].strip()
                        elif line.startswith('priority:'):
                            priority = line.split(':', 1)[1].strip()

            # Log urgency
            urgency_indicator = {
                'URGENT': '🔴',
                'BUSINESS': '🟠',
                'INFO': '🟢',
                'NORMAL': '⚪'
            }.get(urgency, '⚪')

            logger.info(f"⚡ Executing {urgency_indicator} {urgency} action (priority: {priority}): {filepath.name}")

            # Parse action type from filename
            if 'EMAIL' in filepath.name:
                self._execute_email(filepath, content)
            elif 'WHATSAPP' in filepath.name:
                self._execute_whatsapp(filepath, content)
            elif 'PAYMENT' in filepath.name:
                self._execute_payment(filepath, content)
            elif 'INVOICE' in filepath.name:
                self._execute_invoice(filepath, content)
            elif any(platform in filepath.name.upper() for platform in ['POST', 'TWITTER', 'FACEBOOK', 'LINKEDIN', 'INSTAGRAM']):
                self._execute_post(filepath, content)
            else:
                logger.warning(f"Unknown action type: {filepath.name}")

            # Move to done (gracefully handle if file already gone)
            if filepath.exists():
                done_file = self.done / filepath.name
                filepath.rename(done_file)
                logger.info(f"✔️ Done: {done_file.name} [{urgency_indicator} {urgency}]")
                self._log_action('action_executed', filepath.name, 'success', f"urgency={urgency}")
            else:
                logger.warning(f"File already moved or deleted: {filepath.name}")
                self._log_action('action_executed', filepath.name, 'success', f"urgency={urgency} (file already moved)")
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
             
            # Delete the original email from Needs_Action
            self._delete_original_email_from_needs_action(metadata)

        except Exception as e:
            logger.error(f"Email execution failed: {e}")
            raise

    def _delete_original_email_from_needs_action(self, metadata: dict):
        """Move the original email file from Needs_Action to Done after approval is sent"""
        try:
            # Extract gmail_message_id from email draft metadata
            gmail_msg_id = metadata.get('gmail_message_id')
            if not gmail_msg_id:
                logger.debug("No gmail_message_id in metadata - skipping Needs_Action cleanup")
                return

            # Find and move the original EMAIL_*.md file to Done
            original_file = self.needs_action / f"EMAIL_{gmail_msg_id}.md"
            if original_file.exists():
                done_file = self.done / original_file.name
                original_file.rename(done_file)
                logger.info(f"✓ Moved from Needs_Action → Done: {original_file.name}")
            else:
                logger.debug(f"Original email file not found: {original_file}")
        except Exception as e:
            logger.warning(f"Failed to move original email from Needs_Action: {e}")

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
        """Post to Facebook/Instagram via Meta Social MCP"""
        import os
        import json
        import subprocess

        # Support both META_ and FACEBOOK_ naming conventions
        access_token = os.getenv('META_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
        page_id = os.getenv('META_PAGE_ID') or os.getenv('FACEBOOK_PAGE_ID')
        ig_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

        if not access_token:
            raise RuntimeError("META_ACCESS_TOKEN or FACEBOOK_ACCESS_TOKEN not configured in .env")
        if not page_id:
            raise RuntimeError("META_PAGE_ID or FACEBOOK_PAGE_ID not configured in .env")

        try:
            # Determine platform from metadata or default to Facebook
            platform = metadata.get('platform', 'facebook')

            # Call Meta Social MCP
            mcp_path = Path(__file__).parent.parent / 'mcp_servers' / 'meta_social_mcp' / 'index.js'

            if platform in ['instagram', 'ig']:
                if not ig_account_id:
                    raise RuntimeError("INSTAGRAM_BUSINESS_ACCOUNT_ID not configured for Instagram posting")

                tool_request = {
                    'tool': 'post_instagram',
                    'input': {
                        'account_id': ig_account_id,
                        'caption': text,
                        'image_url': metadata.get('image_url', ''),
                        'media_type': 'IMAGE'
                    }
                }
            else:
                # Default to Facebook
                tool_request = {
                    'tool': 'post_facebook',
                    'input': {
                        'page_id': page_id,
                        'message': text,
                        'image_url': metadata.get('image_url'),
                        'link_url': metadata.get('link_url')
                    }
                }

            # Execute via Node.js subprocess
            env = os.environ.copy()
            env['FACEBOOK_ACCESS_TOKEN'] = access_token
            env['FACEBOOK_PAGE_ID'] = page_id
            if ig_account_id:
                env['INSTAGRAM_BUSINESS_ACCOUNT_ID'] = ig_account_id

            process = subprocess.Popen(
                ['node', str(mcp_path), '--legacy-stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            stdout, stderr = process.communicate(input=json.dumps(tool_request), timeout=30)

            if process.returncode != 0 or not stdout.strip():
                logger.error(f"Meta MCP error: {stderr}")
                raise RuntimeError(f"Meta MCP returned error")

            response = json.loads(stdout.strip())

            if not response.get('success'):
                raise RuntimeError(f"Meta API error: {response.get('error', 'Unknown error')}")

            post_id = response.get('post_id')
            platform_name = response.get('platform', 'facebook')

            logger.info(f"✅ Posted to {platform_name.upper()}")
            logger.info(f"   Post ID: {post_id}")

            if platform_name == 'facebook':
                logger.info(f"   URL: https://facebook.com/{post_id}")
            else:
                logger.info(f"   URL: https://instagram.com/p/{post_id}")

            # Log the post
            log_file = self.vault / 'Logs' / 'posts_sent.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            post_log = {
                'text': text,
                'platform': platform_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'posted',
                'post_id': post_id,
                'url': f"https://{platform_name}.com/{post_id}"
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(post_log) + '\n')

            logger.info(f"📝 Logged to: {log_file}")

        except subprocess.TimeoutExpired:
            logger.error("Meta MCP request timed out")
            raise RuntimeError("Meta MCP request timed out")
        except Exception as e:
            logger.error(f"Failed to post via Meta MCP: {e}")
            raise

    def _call_linkedin_api(self, text: str, metadata: dict):
        """Post to LinkedIn via API"""
        import os

        access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')

        if not access_token:
            raise RuntimeError("LINKEDIN_ACCESS_TOKEN not configured in .env")

        try:
            from watchers.linkedin_watcher import LinkedInAPI
            linkedin = LinkedInAPI(access_token)

            # Check for link in metadata
            link_url = metadata.get('url', metadata.get('link', ''))

            if link_url:
                result = linkedin.post_with_link(text, link_url)
            else:
                result = linkedin.post_text(text)

            if result:
                post_id = result.get('id', 'unknown')
                logger.info(f"✅ Posted to LinkedIn")
                logger.info(f"   Post ID: {post_id}")

                # Log the post
                log_file = self.vault / 'Logs' / 'linkedin_posts.jsonl'
                log_file.parent.mkdir(parents=True, exist_ok=True)

                post_log = {
                    'text': text[:200],
                    'platform': 'linkedin',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': 'posted',
                    'post_id': post_id
                }

                with open(log_file, 'a') as f:
                    f.write(json.dumps(post_log) + '\n')

                logger.info(f"📝 Logged to: {log_file}")
            else:
                raise RuntimeError("LinkedIn post returned no result")

        except ImportError:
            raise RuntimeError("LinkedIn watcher not available")
        except Exception as e:
            logger.error(f"Failed to post to LinkedIn: {e}")
            raise

    def _execute_whatsapp(self, filepath, content):
        """Execute WhatsApp action - Send reply via WhatsApp Business API"""
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

            # Extract reply text from ## Proposed Reply section
            reply_text = ''
            reply_started = False
            reply_sections = ['## Proposed Reply', '## Your Reply', '## Reply']

            for line in lines[frontmatter_end:]:
                if any(section in line for section in reply_sections):
                    reply_started = True
                    continue
                elif reply_started and line.startswith('##'):
                    break
                elif reply_started:
                    reply_text += line + '\n'

            reply_text = reply_text.strip()

            # Get recipient phone number
            recipient = metadata.get('to', metadata.get('from', ''))

            if not reply_text:
                raise ValueError("No reply text found in ## Proposed Reply section")

            if not recipient:
                raise ValueError("No recipient phone number found in 'to:' or 'from:' field")

            logger.info(f"💬 Sending WhatsApp message to {recipient}")
            logger.info(f"   Message preview: {reply_text[:100]}...")

            # Send via WhatsApp Business API
            if self.whatsapp_api:
                self.whatsapp_api.send_message(recipient, reply_text)
                logger.info(f"✅ WhatsApp message sent successfully to {recipient}")
            else:
                raise RuntimeError("WhatsApp Business API not initialized")

            # Delete the original WhatsApp message from Needs_Action
            self._delete_original_whatsapp_from_needs_action(metadata)

        except Exception as e:
            logger.error(f"WhatsApp execution failed: {e}")
            raise

    def _delete_original_whatsapp_from_needs_action(self, metadata: dict):
        """Move the original WhatsApp message from Needs_Action to Done after reply is sent"""
        try:
            # Extract original_file from WhatsApp draft metadata
            original_file = metadata.get('original_file')
            if not original_file:
                logger.debug("No original_file in metadata - skipping Needs_Action cleanup")
                return

            # Find and move the original WHATSAPP_*.md file to Done
            original_path = self.needs_action / original_file
            if original_path.exists():
                done_path = self.done / original_path.name
                original_path.rename(done_path)
                logger.info(f"✓ Moved from Needs_Action → Done: {original_path.name}")
            else:
                logger.debug(f"Original WhatsApp message not found: {original_path}")
        except Exception as e:
            logger.warning(f"Failed to move original WhatsApp message from Needs_Action: {e}")

    def _execute_payment(self, filepath, content):
        """Execute payment action - Log transaction via Xero MCP"""
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

            # Extract payment details from content
            amount = metadata.get('amount', '0')
            description = metadata.get('description', 'Payment from orchestrator')
            account = metadata.get('account', '200')  # Default to sales revenue
            transaction_type = metadata.get('transaction_type', 'BANK')
            bank_account_code = metadata.get('bank_account_code', metadata.get('bank_account', ''))

            logger.info(f"💰 Processing payment: {description}")
            logger.info(f"   Amount: {amount}")
            logger.info(f"   Account: {account}")

            # Call Xero MCP to log transaction
            self._call_xero_mcp_log_transaction(
                float(amount),
                description,
                account,
                transaction_type,
                bank_account_code=bank_account_code
            )

            logger.info(f"✅ Payment logged successfully")

        except Exception as e:
            logger.error(f"Payment execution failed: {e}")
            raise

    def _call_xero_mcp_log_transaction(
        self,
        amount: float,
        description: str,
        account: str,
        transaction_type: str = 'BANK',
        bank_account_code: str = ''
    ):
        """Log transaction via Xero MCP server"""
        import os
        import json
        import subprocess

        try:
            xero_access_token = os.getenv('XERO_ACCESS_TOKEN')
            xero_tenant_id = os.getenv('XERO_TENANT_ID')

            if not xero_access_token or not xero_tenant_id:
                logger.warning("Xero credentials not configured - missing XERO_ACCESS_TOKEN or XERO_TENANT_ID")
                return

            # Create request for Xero MCP
            mcp_path = Path(__file__).parent.parent / 'mcp_servers' / 'xero_mcp' / 'index.js'

            tool_request = {
                'tool': 'log_transaction',
                'input': {
                    'amount': amount,
                    'description': description,
                    'account': account,
                    'transaction_type': transaction_type,
                    'bank_account_code': bank_account_code,
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            }

            # Execute via Node.js subprocess
            env = os.environ.copy()
            env['XERO_ACCESS_TOKEN'] = xero_access_token
            env['XERO_TENANT_ID'] = xero_tenant_id

            process = subprocess.Popen(
                ['node', str(mcp_path), '--legacy-stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            stdout, stderr = process.communicate(input=json.dumps(tool_request), timeout=30)

            if process.returncode != 0 or not stdout.strip():
                logger.warning(f"Xero MCP returned non-zero status: {stderr}")
                return

            response = json.loads(stdout.strip())

            if not response.get('status') or response.get('status') == 'error':
                error = response.get('error', 'Unknown error')
                detail = response.get('detail')
                if detail:
                    logger.warning(f"Xero transaction logging returned: {error} ({detail})")
                else:
                    logger.warning(f"Xero transaction logging returned: {error}")
                return

            transaction_id = response.get('transaction_id', 'unknown')
            logger.info(f"✅ Transaction logged in Xero (ID: {transaction_id})")

            # Log the transaction
            log_file = self.vault / 'Logs' / 'xero_transactions.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            txn_log = {
                'amount': amount,
                'description': description,
                'account': account,
                'transaction_type': transaction_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'logged',
                'transaction_id': transaction_id
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(txn_log) + '\n')

        except subprocess.TimeoutExpired:
            logger.error("Xero MCP request timed out")
        except Exception as e:
            logger.warning(f"Failed to log transaction via Xero MCP: {e}")

    def _execute_invoice(self, filepath, content):
        """Execute invoice action - Create invoice in Xero MCP"""
        try:
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

            contact_name = metadata.get('contact_name') or metadata.get('contact') or ''
            amount_raw = metadata.get('amount', '').strip()
            description = metadata.get('description', 'Invoice from orchestrator')
            due_date = metadata.get('due_date', '')

            if not contact_name:
                raise ValueError("Missing contact_name in invoice draft")
            if not amount_raw:
                raise ValueError("Missing amount in invoice draft")

            amount = float(amount_raw)
            logger.info(f"🧾 Creating Xero invoice for {contact_name} ({amount:.2f})")

            self._call_xero_mcp_create_invoice(contact_name, amount, description, due_date)
            logger.info("✅ Invoice created successfully")

        except Exception as e:
            logger.error(f"Invoice execution failed: {e}")
            raise

    def _call_xero_mcp_create_invoice(self, contact_name, amount, description, due_date):
        """Create invoice via Xero MCP server"""
        import os
        import json
        import subprocess

        try:
            xero_access_token = os.getenv('XERO_ACCESS_TOKEN')
            xero_tenant_id = os.getenv('XERO_TENANT_ID')

            if not xero_access_token or not xero_tenant_id:
                logger.warning("Xero credentials not configured - missing XERO_ACCESS_TOKEN or XERO_TENANT_ID")
                return

            mcp_path = Path(__file__).parent.parent / 'mcp_servers' / 'xero_mcp' / 'index.js'

            tool_request = {
                'tool': 'create_invoice',
                'input': {
                    'contact_name': contact_name,
                    'amount': amount,
                    'description': description,
                    'due_date': due_date or (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                }
            }

            env = os.environ.copy()
            env['XERO_ACCESS_TOKEN'] = xero_access_token
            env['XERO_TENANT_ID'] = xero_tenant_id

            process = subprocess.Popen(
                ['node', str(mcp_path), '--legacy-stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            stdout, stderr = process.communicate(input=json.dumps(tool_request), timeout=30)

            if process.returncode != 0 or not stdout.strip():
                logger.warning(f"Xero MCP returned non-zero status: {stderr}")
                return

            response = json.loads(stdout.strip())
            if response.get('status') != 'created':
                error = response.get('error', 'Unknown error')
                detail = response.get('detail')
                if detail:
                    logger.warning(f"Xero invoice creation returned: {error} ({detail})")
                else:
                    logger.warning(f"Xero invoice creation returned: {error}")
                return

            invoice_id = response.get('invoice_id', 'unknown')
            logger.info(f"✅ Invoice created in Xero (ID: {invoice_id})")

        except subprocess.TimeoutExpired:
            logger.error("Xero MCP request timed out")
        except Exception as e:
            logger.warning(f"Failed to create invoice via Xero MCP: {e}")
    
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

            # Determine platforms from metadata or filename
            # Support both 'platform:' (single) and 'platforms:' (multiple)
            platforms_str = metadata.get('platforms', metadata.get('platform', '')).lower()
            platforms = [p.strip() for p in platforms_str.split(',') if p.strip()]

            # Fallback: check filename for platform hints
            if not platforms:
                if 'facebook' in filepath.name.lower() or 'fb' in filepath.name.lower():
                    platforms = ['facebook']
                elif 'linkedin' in filepath.name.lower() or 'li' in filepath.name.lower():
                    platforms = ['linkedin']
                elif 'instagram' in filepath.name.lower() or 'ig' in filepath.name.lower():
                    platforms = ['instagram']
                else:
                    platforms = ['linkedin', 'facebook']  # Default to LinkedIn + Facebook

            # Extract post text - support formats: ## Proposed Post, ## Tweet, ## Post Text, ## Post Content, ## Content
            post_text = ''
            post_started = False
            post_sections = ['## Proposed Post', '## Tweet', '## Post Text', '## Post Content', '## Facebook Post', '## Content']

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

            # Route to all specified platforms
            for platform in platforms:
                try:
                    if platform == 'twitter':
                        tweet_text = post_text
                        if len(tweet_text) > 280:
                            logger.warning(f"Tweet exceeds 280 chars ({len(tweet_text)}), truncating")
                            tweet_text = tweet_text[:277] + "..."

                        logger.info(f"📱 Posting to Twitter/X")
                        self._call_twitter_api(tweet_text, metadata)
                        logger.info(f"✅ Tweet posted successfully")

                    elif platform in ['facebook', 'fb']:
                        logger.info(f"📘 Posting to Facebook")
                        self._call_meta_api(post_text, metadata)
                        logger.info(f"✅ Facebook post successful")

                    elif platform == 'linkedin':
                        logger.info(f"💼 Posting to LinkedIn")
                        self._call_linkedin_api(post_text, metadata)
                        logger.info(f"✅ LinkedIn post successful")

                    elif platform in ['instagram', 'ig']:
                        logger.info(f"📸 Posting to Instagram")
                        # Add platform info to metadata for Meta MCP
                        metadata['platform'] = 'instagram'
                        self._call_meta_api(post_text, metadata)
                        logger.info(f"✅ Instagram post successful")

                    else:
                        logger.warning(f"Unknown platform: {platform}, skipping")

                except Exception as e:
                    logger.error(f"Failed to post to {platform}: {e}")

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
    
    # Track last Xero token refresh
    last_xero_refresh = time.time()
    xero_refresh_interval = 1200  # Refresh every 20 minutes (token valid for 30 min)

    try:
        while True:
            # Periodically flush batches to ensure timely processing
            current_time = time.time()
            if (current_time - handler.last_batch_time) > handler.batch_timeout:
                for queue_type in ['inbox', 'approved']:
                    if handler.event_queue[queue_type]:
                        handler._process_batch(queue_type)

            # Periodically refresh Xero token to prevent expiration
            if (current_time - last_xero_refresh) > xero_refresh_interval:
                handler._refresh_xero_token_if_needed()
                last_xero_refresh = current_time

            # Periodically scan Approved folder for any files that weren't caught by watchdog
            if (current_time - last_approved_scan) > approved_scan_interval:
                approved_files = [f for f in handler.approved.glob('*.md') if f.name != '.gitkeep']
                for filepath in approved_files:
                    # Skip if already executed (prevents duplicate sends)
                    if filepath.name in handler.executed_files:
                        logger.debug(f"Periodic scan: Skipping already-executed file: {filepath.name}")
                        continue
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
