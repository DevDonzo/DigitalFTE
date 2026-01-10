"""Email Drafter - OpenAI-powered autonomous response generation"""
import os
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

class EmailDrafter:
    """Uses OpenAI API to intelligently draft email responses"""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'
        self.pending = self.vault / 'Pending_Approval'
        self.handbook = self.vault / 'Company_Handbook.md'
        self.processed_emails_file = self.vault / '.processed_emails'
        self.processed_emails = self._load_processed_emails()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.client = None
        self.client_type = None

        # Initialize OpenAI client
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.client_type = "openai"
                logger.info("✓ OpenAI initialized (gpt-4o-mini)")
                return
            except ImportError:
                logger.error("OpenAI SDK not installed. Install: pip install openai")
                pass

        # No API key or SDK available - will use fallback templates
        logger.warning("OPENAI_API_KEY not set or SDK not installed")
        logger.warning("Email drafting will use fallback template responses")
        logger.warning("Install SDK: pip install openai")
        self.client = None

    def _load_processed_emails(self) -> set:
        """Load set of already-processed email filenames"""
        if self.processed_emails_file.exists():
            return set(self.processed_emails_file.read_text().strip().split('\n'))
        return set()

    def _mark_email_processed(self, email_filename: str):
        """Track that this email has been processed"""
        self.processed_emails.add(email_filename)
        with open(self.processed_emails_file, 'a') as f:
            f.write(email_filename + '\n')

    def _load_handbook_rules(self) -> dict:
        """Load automation rules from Company_Handbook.md"""
        if not self.handbook.exists():
            return {}

        handbook_text = self.handbook.read_text()

        # Parse known contacts
        known_contacts = []
        if "Known Contacts" in handbook_text:
            section = handbook_text.split("Known Contacts")[1].split("**Response Rules")[0]
            for line in section.split('\n'):
                if line.strip().startswith('- '):
                    email = line.strip().lstrip('- ')
                    known_contacts.append(email)

        return {
            'known_contacts': known_contacts,
            'handbook_text': handbook_text
        }

    def _parse_email(self, email_file: Path) -> dict:
        """Parse markdown email file"""
        content = email_file.read_text()

        # Parse frontmatter
        parts = content.split('---')
        metadata = {}

        if len(parts) >= 2:
            frontmatter = parts[1]
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()

        # Extract body sections
        body = ''.join(parts[2:]) if len(parts) > 2 else ''

        return {
            'filename': email_file.name,
            'from': metadata.get('from', 'Unknown'),
            'subject': metadata.get('subject', 'No Subject'),
            'received': metadata.get('received', ''),
            'priority': metadata.get('priority', 'normal'),
            'body': body
        }

    def _classify_email_type(self, email: dict, handbook_rules: dict) -> Tuple[str, bool]:
        """Classify email type and determine if auto-approve is possible"""
        subject = email['subject'].lower()
        sender = email['from'].lower()

        # Check if known contact
        known_contacts = handbook_rules.get('known_contacts', [])
        is_known = any(contact.lower() in sender for contact in known_contacts)

        # Classify by subject keywords
        if any(word in subject for word in ['meeting', 'schedule', 'calendar', 'time?']):
            email_type = 'meeting_request'
        elif any(word in subject for word in ['invoice', 'payment', 'bill', 'receipt']):
            email_type = 'invoice'
        elif any(word in subject for word in ['problem', 'issue', 'complaint', 'error', 'broken']):
            email_type = 'complaint'
        elif any(word in subject for word in ['question', 'inquiry', 'help', 'info', 'can you']):
            email_type = 'inquiry'
        else:
            email_type = 'general'

        # HITL WORKFLOW: All emails require manual approval - no auto-approve
        # User reviews in /Pending_Approval and drags to /Approved to send
        auto_approve = False

        return email_type, auto_approve

    def _generate_draft(self, email: dict, email_type: str, handbook_rules: dict) -> Tuple[str, float]:
        """Use OpenAI to generate email response draft"""

        if not self.client or not self.model:
            logger.warning("OpenAI not configured - using template response")
            return self._generate_template_response(email), 0.0

        # Build prompt
        handbook_excerpt = handbook_rules.get('handbook_text', '')[:1000]

        prompt = f"""You are an AI assistant drafting professional email responses.
Your task is to draft a reply to the following email based on the company automation rules.

COMPANY RULES:
{handbook_excerpt}

INCOMING EMAIL:
From: {email['from']}
Subject: {email['subject']}
Type: {email_type}

Body:
{email['body'][:500]}

TASK:
1. Understand the intent of the email
2. Draft a professional, concise response (2-3 paragraphs)
3. Match the company tone (professional but friendly)
4. End with appropriate closing

RESPONSE FORMAT:
Provide ONLY the email body text, no formatting. This will be sent as-is.
Keep it professional and helpful. 2-4 sentences per paragraph."""

        try:
            # Call OpenAI API
            if self.client_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """You are Hamza Paracha's AI Reasoning Engine - an autonomous assistant that drafts professional email responses on his behalf.

CORE RESPONSIBILITIES:
1. Analyze incoming emails using reasoning to understand intent and context
2. Reference Company_Handbook.md rules for appropriate response type and tone
3. Draft responses that are professional, factual, and aligned with business goals
4. Flag complex or sensitive emails for human review (low confidence < 80%)

RESPONSE GUIDELINES BY EMAIL TYPE:
- **Inquiry**: Professional tone, factual information, concise, <2 hour response time
- **Complaint**: Empathetic, acknowledge concern, propose solution, maintain professionalism
- **Invoice/Payment**: Factual, include reference numbers, professional acknowledgment
- **Meeting Request**: Confirmatory tone, check calendar context if available, positive
- **New Contact**: Warm but cautious, professional introduction, no commitments

AUTOMATION RULES TO FOLLOW:
- Known contacts (boss@company.com, team@company.com, etc): Auto-approve appropriate responses
- New/Unknown contacts: Flag for human review
- Non-business topics: Always require human approval
- Complex decisions: Flag low confidence drafts (<80%) for review
- Financial/sensitive: Always escalate for approval

SAFETY & COMPLIANCE:
- Include disclosure: "This reply was drafted by Hamza Paracha's AI Assistant"
- Always reference your reasoning (why this response type)
- Never make commitments or promises on behalf of Hamza
- When unsure, err on side of escalation to human
- Maintain professional, business-appropriate tone at all times

Your responses should be clear, concise, and professional. Sign off with 'Hamza Paracha's AI Assistant'."""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                draft = response.choices[0].message.content
            else:
                # Shouldn't happen, but fallback just in case
                return self._generate_template_response(email), 0.7

            confidence = 0.90  # OpenAI responses are generally high confidence
            logger.info(f"✓ Draft generated via OpenAI API ({self.model})")
            return draft, confidence

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            logger.warning("Falling back to template response")
            return self._generate_template_response(email), 0.7

    def _generate_template_response(self, email: dict) -> str:
        """Fallback template response if Gemini is unavailable"""
        subject = email['subject']
        sender = email['from'].split('@')[0]

        return f"""Hi {sender.title()},

Thank you for your email regarding "{subject}".

I've reviewed your message and will provide a detailed response shortly.

Best regards,
Hamza Paracha's AI Assistant"""

    def _create_draft_file(self, email: dict, email_type: str, draft_response: str,
                          confidence: float, auto_approve: bool) -> Path:
        """Create draft approval file in Pending_Approval/ or Approved/ if auto-approve"""

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f"EMAIL_DRAFT_{timestamp}.md"
        # If auto-approved, send directly to Approved folder for immediate sending
        draft_path = self.vault / 'Approved' / draft_filename if auto_approve else self.pending / draft_filename

        # Build draft file content
        draft_content = f"""---
type: email_draft
original_from: {email['from']}
original_subject: {email['subject']}
email_type: {email_type}
created: {datetime.now().isoformat()}
auto_approve: {str(auto_approve).lower()}
confidence: {confidence:.2f}
ai_generated: true
---

## Original Email

**From**: {email['from']}
**Subject**: {email['subject']}
**Received**: {email['received']}
**Priority**: {email['priority']}

### Body
{email['body']}

---

## AI Analysis

**Email Type**: {email_type}
**Confidence**: {confidence*100:.0f}%
**Auto-Approve**: {auto_approve}

**AI Assistant's Reasoning**:
- Classified as {email_type} based on subject keywords and sender
- Sender: {email['from']}
- Suggested tone: Professional and helpful
- Response length: ~3 paragraphs

---

## Proposed Response

{draft_response}

---

## AI Disclosure Signature

*This email reply was drafted by Hamza Paracha's AI Assistant.*
*Hamza Paracha reviewed and approved this response.*
*Sent via DigitalFTE autonomous email system.*

---

## Actions

{'- [x] Auto-approved (known contact)' if auto_approve else '- [ ] Requires manual approval'}
- [ ] Review and edit response above
- [ ] Move to /Approved/ folder to send
- [ ] Reject (send custom reply instead)

**Instructions**:
1. If auto-approved: Just move this file to /Approved/ to send
2. If requires approval: Review the draft, optionally edit, then move to /Approved/
3. If you want to reject: Delete this file and create your own reply

---

*Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # Write draft file (ensure directory exists)
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(draft_content)
        if auto_approve:
            logger.info(f"✓ Draft auto-approved and queued to send: {draft_filename}")
        else:
            logger.info(f"✓ Draft created (pending approval): {draft_filename}")

        return draft_path

    def draft_reply(self, email_file: Path) -> Optional[Path]:
        """Main entry point: Draft a reply to an incoming email"""

        if not email_file.exists():
            logger.error(f"Email file not found: {email_file}")
            return None

        # Check if this email has already been processed
        if email_file.name in self.processed_emails:
            logger.debug(f"⏭️  Skipping already-processed email: {email_file.name}")
            return None

        logger.info(f"📧 Drafting reply for: {email_file.name}")

        # Parse email
        email = self._parse_email(email_file)
        logger.debug(f"  From: {email['from']}")
        logger.debug(f"  Subject: {email['subject']}")

        # Load rules
        handbook_rules = self._load_handbook_rules()

        # Classify email
        email_type, auto_approve = self._classify_email_type(email, handbook_rules)
        logger.debug(f"  Type: {email_type}, Auto-approve: {auto_approve}")

        # Generate draft via Claude
        draft_response, confidence = self._generate_draft(email, email_type, handbook_rules)

        # Create approval file
        draft_path = self._create_draft_file(email, email_type, draft_response, confidence, auto_approve)

        # Mark as processed
        self._mark_email_processed(email_file.name)

        return draft_path


# CLI for testing
if __name__ == '__main__':
    import sys

    vault_path = os.getenv('VAULT_PATH', './vault')

    if len(sys.argv) < 2:
        print("Usage: python email_drafter.py <email_file_path>")
        print(f"Example: python email_drafter.py vault/Inbox/EMAIL_001.md")
        sys.exit(1)

    email_file = Path(sys.argv[1])

    drafter = EmailDrafter(vault_path)
    result = drafter.draft_reply(email_file)

    if result:
        print(f"✅ Draft created: {result}")
    else:
        print("❌ Failed to create draft")
