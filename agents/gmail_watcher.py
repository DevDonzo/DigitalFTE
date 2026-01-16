"""Gmail Watcher - Real implementation using google-auth-oauthlib"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
try:
    from .base_watcher import BaseWatcher
except ImportError:
    from base_watcher import BaseWatcher

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Install google-auth-oauthlib and google-api-python-client")
    print("pip install google-auth-oauthlib google-api-python-client")

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: Install openai")
    print("pip install openai")

# Load env vars
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailWatcher(BaseWatcher):
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=20)
        self.service = self._authenticate()

        # Initialize OpenAI for smart email filtering
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.ai_client = OpenAI(api_key=api_key)
            logger.info("✓ AI-powered email filtering enabled")
        else:
            self.ai_client = None
            logger.warning("⚠️  OpenAI API key not found - using basic filtering")
    
    def _get_client_config(self) -> dict:
        """Build OAuth client config from environment variables"""
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        project_id = os.getenv('GMAIL_PROJECT_ID', 'gmail-watcher')
        
        if not client_id or not client_secret:
            raise ValueError("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env")
        
        return {
            "installed": {
                "client_id": client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }
        
    def _authenticate(self):
        """Authenticate with Gmail API using environment variables"""
        try:
            creds = None
            token_file = Path.home() / '.gmail_token.json'
            
            # Load existing token
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            # Refresh if needed
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            # New auth flow using config from env vars
            if not creds or not creds.valid:
                client_config = self._get_client_config()
                flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None
    
    def _should_reply_to_email(self, msg) -> bool:
        """Use AI to intelligently determine if this email is from a real person (not spam/automated)"""
        if not self.ai_client:
            return True  # Default to include if AI not available

        try:
            headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
            subject = headers.get('subject', '')
            sender = headers.get('from', '')
            body = self._get_email_body(msg.get('payload', ''))[:2000]  # Limit to 2000 chars

            # Use AI to analyze if this is from a real person or automated system
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an email filter that determines if an email is from a REAL PERSON or an AUTOMATED SYSTEM.

Return only "HUMAN" or "BOT".

Return BOT for:
- No-reply addresses (noreply@, donotreply@, automated@, etc)
- System notifications (password reset, verification, alerts)
- Transactional emails (receipts, confirmations, invoices, shipping)
- Automated responses (out of office, auto-reply, undeliverable)
- Marketing/bulk emails (newsletters, promotional, surveys)
- Explicitly says "do not reply"

Return HUMAN for:
- Emails from real people (even if brief like "Hi" or "Yes")
- Questions or requests
- Conversations from colleagues/friends/contacts
- Anything that seems personally addressed to you
- When in doubt, assume HUMAN (don't be aggressive)"""
                    },
                    {
                        "role": "user",
                        "content": f"""Email Analysis:

From: {sender}
Subject: {subject}
Body: {body}

Is this from a HUMAN or a BOT/AUTOMATED SYSTEM?"""
                    }
                ],
                temperature=0.3,
                max_tokens=10
            )

            decision = response.choices[0].message.content.strip().upper()
            return "HUMAN" in decision

        except Exception as e:
            logger.error(f"AI filtering error: {e}")
            return True  # Default to include if AI fails

    def check_for_updates(self) -> list:
        """Check for unread important emails - filter for human-relevant ones"""
        if not self.service:
            return []

        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread is:important', maxResults=10
            ).execute()
            messages = results.get('messages', [])

            filtered_messages = []
            for m in messages:
                if m['id'] in self.processed_ids:
                    continue

                # Get full message to check with AI
                try:
                    full_msg = self.service.users().messages().get(
                        userId='me', id=m['id'], format='full'
                    ).execute()

                    if self._should_reply_to_email(full_msg):
                        filtered_messages.append(m)
                    else:
                        # Not a human email - skip this
                        self.processed_ids.add(m['id'])
                        headers = {h['name'].lower(): h['value'] for h in full_msg['payload'].get('headers', [])}
                        logger.info(f"⏭️  Spam/Auto (skipped): {headers.get('subject', 'No Subject')} from {headers.get('from', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error checking email {m['id']}: {e}")
                    filtered_messages.append(m)  # Default to include if we can't check

            return filtered_messages
        except Exception as e:
            logger.error(f"Gmail check error: {e}")
            return []
      
    def _get_email_body(self, payload) -> str:
        """Extract full email body from Gmail payload"""
        import base64

        body = ""

        # Check for direct body
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

        # Check for multipart
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
                elif mime_type == 'text/html' and part.get('body', {}).get('data') and not body:
                    # Fallback to HTML if no plain text
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    # Basic HTML stripping
                    import re
                    body = re.sub('<[^<]+?>', '', html)
                elif 'parts' in part:
                    # Nested multipart
                    nested_body = self._get_email_body(part)
                    if nested_body:
                        body = nested_body
                        break

        return body.strip()[:5000]  # Limit to 5000 chars

    def _get_email_thread(self, thread_id: str) -> list[dict]:
        """Fetch full thread conversation from Gmail"""
        try:
            thread = self.service.users().threads().get(
                userId='me', id=thread_id, format='full'
            ).execute()

            messages = []
            for msg in thread.get('messages', []):
                headers = {h['name'].lower(): h['value']
                          for h in msg['payload'].get('headers', [])}
                body = self._get_email_body(msg.get('payload', {}))

                messages.append({
                    'from': headers.get('from', 'Unknown'),
                    'date': headers.get('date', ''),
                    'subject': headers.get('subject', ''),
                    'body': body
                })

            logger.debug(f"✓ Fetched thread {thread_id} with {len(messages)} message(s)")
            return messages
        except Exception as e:
            logger.error(f"Failed to fetch thread {thread_id}: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """Create markdown file for new email"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id'], format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            snippet = msg.get('snippet', '')
            thread_id = msg.get('threadId', '')

            # Get full body
            full_body = self._get_email_body(msg.get('payload', {}))
            if not full_body:
                full_body = snippet

            # Fetch thread context if this is part of a thread
            thread_messages = []
            is_reply = False
            if thread_id:
                thread_messages = self._get_email_thread(thread_id)
                is_reply = len(thread_messages) > 1

            # Build thread history section if this is a reply
            thread_history_section = ""
            if is_reply and thread_messages:
                thread_history_section = "\n## Thread History (Oldest to Newest)\n\n"
                # Show all messages except the current one (last message)
                for i, tmsg in enumerate(thread_messages[:-1], 1):
                    thread_history_section += f"### Message {i}: {tmsg['date']} from {tmsg['from']}\n\n"
                    thread_history_section += f"{tmsg['body']}\n\n"
                    thread_history_section += "---\n\n"

            content = f"""---
type: email
gmail_message_id: {message['id']}
thread_id: {thread_id}
is_reply: {str(is_reply).lower()}
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## From
{headers.get('From', 'Unknown')}

## Subject
{headers.get('Subject', 'No Subject')}

{thread_history_section}

## Current Message
{full_body}

## Actions
- [ ] Reply
- [ ] Forward
- [ ] Archive
"""
            filepath = self.needs_action / f"EMAIL_{message['id']}.md"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
            self.processed_ids.add(message['id'])
            logger.info(f"Created: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return None

    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read in Gmail"""
        if not self.service:
            return False

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"✓ Marked as read in Gmail: {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark as read: {e}")
            return False

if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    
    # Validate required env vars
    if not os.getenv('GMAIL_CLIENT_ID') or not os.getenv('GMAIL_CLIENT_SECRET'):
        print("ERROR: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env")
        print("Get these from Google Cloud Console: https://console.cloud.google.com/")
        exit(1)
    
    watcher = GmailWatcher(vault_path)
    watcher.run()
