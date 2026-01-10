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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailWatcher(BaseWatcher):
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)
        self.credentials_path = Path(credentials_path)
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Gmail API"""
        try:
            creds = None
            token_file = Path.home() / '.gmail_token.json'
            
            # Load existing token
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            # Refresh if needed
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            # New auth flow
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None
    
    def check_for_updates(self) -> list:
        """Check for unread important emails"""
        if not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread is:important', maxResults=5
            ).execute()
            messages = results.get('messages', [])
            return [m for m in messages if m['id'] not in self.processed_ids]
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

    def create_action_file(self, message) -> Path:
        """Create markdown file for new email"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id'], format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            snippet = msg.get('snippet', '')

            # Get full body
            full_body = self._get_email_body(msg.get('payload', {}))
            if not full_body:
                full_body = snippet

            content = f"""---
type: email
gmail_message_id: {message['id']}
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

## Body
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
    creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    
    if not Path(creds_path).exists():
        print(f"ERROR: credentials.json not found at {creds_path}")
        print("Download from Google Cloud Console: https://console.cloud.google.com/")
        exit(1)
    
    watcher = GmailWatcher(vault_path, creds_path)
    watcher.run()
