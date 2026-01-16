"""Email Style Analyzer - Learns user's email writing style from sent emails"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

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
    print("ERROR: Install google-auth-oauthlib and google-api-python-client")
    print("pip install google-auth-oauthlib google-api-python-client")

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: Install openai")
    print("pip install openai")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailStyleAnalyzer:
    """Analyze sent emails to extract writing style patterns"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.gmail_service = self._authenticate()

        # Initialize OpenAI for style analysis
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.ai_client = OpenAI(api_key=api_key)
            logger.info("✓ OpenAI client initialized")
        else:
            logger.error("OPENAI_API_KEY not found - cannot analyze style")
            self.ai_client = None

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

    def _get_email_body(self, payload) -> str:
        """Extract email body from Gmail payload"""
        if 'parts' not in payload:
            if 'data' in payload.get('body', {}):
                import base64
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            return ""

        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part.get('body', {}):
                    import base64
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

        return ""

    def _fetch_sent_emails(self, max_results: int = 30) -> list[dict]:
        """Fetch recent sent emails from Gmail"""
        try:
            results = self.gmail_service.users().messages().list(
                userId='me', q='in:sent', maxResults=max_results
            ).execute()

            message_ids = [msg['id'] for msg in results.get('messages', [])]
            logger.info(f"✓ Found {len(message_ids)} sent emails")

            emails = []
            for msg_id in message_ids:
                try:
                    msg = self.gmail_service.users().messages().get(
                        userId='me', id=msg_id, format='full'
                    ).execute()

                    headers = {h['name'].lower(): h['value']
                              for h in msg['payload'].get('headers', [])}

                    body = self._get_email_body(msg.get('payload', {}))

                    emails.append({
                        'subject': headers.get('subject', ''),
                        'to': headers.get('to', ''),
                        'date': headers.get('date', ''),
                        'body': body[:2000]  # Limit to 2000 chars for analysis
                    })
                except Exception as e:
                    logger.error(f"Error fetching message {msg_id}: {e}")
                    continue

            return emails
        except Exception as e:
            logger.error(f"Failed to fetch sent emails: {e}")
            return []

    def _analyze_style(self, emails: list[dict]) -> str:
        """Use OpenAI to analyze writing style from emails"""
        if not self.ai_client or not emails:
            return ""

        # Prepare email samples for analysis
        email_samples = "\n\n---\n\n".join([
            f"Subject: {e['subject']}\n\nBody:\n{e['body']}"
            for e in emails[:10]  # Analyze first 10 emails
        ])

        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these sample emails and describe the writer's email style. Return a comprehensive style guide with these sections:

SAMPLE EMAILS:
{email_samples}

---

Provide analysis in this format (markdown):

# Email Writing Style Guide

## Tone & Voice
[Describe the overall tone - formal, conversational, casual, etc.]
[Mention key characteristics]

## Opening Lines
[List 3-5 typical opening phrases the writer uses]

## Common Phrases & Transitions
[List favorite transitional phrases and expressions]

## Closing Signature
[Describe how the writer closes emails]

## Sentence Structure
[Describe whether sentences are short/long, simple/complex]

## Paragraph Style
[Describe typical paragraph length and structure]

## Key Characteristics
[List unique writing habits or patterns]

## Do's
[List things this writer typically does]

## Don'ts
[List things this writer avoids]

## Example Closing
[Show a typical sign-off/closing format]

Be specific and practical. This will be used to train an AI to write emails matching this style."""
                }],
                temperature=0.5,
                max_tokens=1500
            )

            style_guide = response.choices[0].message.content
            logger.info("✓ Style analysis complete")
            return style_guide

        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return ""

    def create_style_guide(self, output_path: str = None) -> Path:
        """Generate EmailStyle.md from sent emails"""
        if not self.gmail_service:
            logger.error("Gmail service not initialized")
            return None

        if not self.ai_client:
            logger.error("OpenAI client not initialized")
            return None

        # Fetch sent emails
        logger.info("📧 Fetching your sent emails...")
        emails = self._fetch_sent_emails(max_results=30)

        if not emails:
            logger.error("No sent emails found or failed to fetch")
            return None

        # Analyze style
        logger.info("🔍 Analyzing your writing style...")
        style_guide = self._analyze_style(emails)

        if not style_guide:
            logger.error("Failed to analyze style")
            return None

        # Save to vault
        output_file = output_path or str(self.vault / 'EmailStyle.md')
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build final markdown with metadata
        content = f"""# Your Email Writing Style

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Source**: Analysis of {len(emails)} recent sent emails
**Note**: You can edit this file anytime to refine your style guide

---

{style_guide}

---

## How This Guide is Used

Your AI Email Assistant will use this style guide when drafting responses to match your natural writing voice. The more specific and accurate this guide, the better the AI can match your tone and style.

### Tips for Improvement

1. Review the generated guide and edit sections that don't feel accurate
2. Add specific phrases or patterns not captured
3. Note any context-specific variations (e.g., "more casual with friends, more formal with clients")
4. Re-run this analyzer periodically as your style evolves

---

**Auto-generated by EmailStyleAnalyzer**
"""

        output_path.write_text(content)
        logger.info(f"✅ Style guide created: {output_path}")

        return output_path


def main():
    """CLI entry point"""
    import sys

    vault_path = os.getenv('VAULT_PATH', './vault')

    # Check for required environment variables
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env")
        print("\n📝 To get credentials:")
        print("   1. Go to Google Cloud Console")
        print("   2. Create OAuth 2.0 Client ID (Desktop app)")
        print("   3. Copy Client ID and Client Secret to .env")
        sys.exit(1)

    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not set in .env")
        print("\n📝 Set it in your .env file: OPENAI_API_KEY=your_key_here")
        sys.exit(1)

    print("\n📊 Email Style Analyzer")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print(f"Gmail Client ID: {client_id[:20]}...")
    print("=" * 50 + "\n")

    analyzer = EmailStyleAnalyzer(vault_path)
    result = analyzer.create_style_guide()

    if result:
        print(f"\n✅ Success! Style guide saved to: {result}")
        print("\n📖 You can now review and edit the file:")
        print(f"   cat {result}")
    else:
        print("\n❌ Failed to create style guide")
        sys.exit(1)


if __name__ == '__main__':
    main()
