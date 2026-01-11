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

        # Build prompt - include full email body for context
        prompt = f"""INCOMING EMAIL:
From: {email['from']}
Subject: {email['subject']}

{email['body']}

---

INSTRUCTIONS:
1. Read the ENTIRE email above carefully
2. Identify EVERY question asked (numbered or implied)
3. Address EACH question explicitly in your response
4. For questions requiring Hamza's input (rates, specific dates, commitments), say you'll confirm with Hamza
5. Be direct and to-the-point - no filler phrases
6. Keep response professional but friendly

RESPONSE FORMAT:
- Start with a brief greeting/acknowledgment (1 sentence max)
- Address each question/request in order
- End with clear next steps
- Use the sign-off format from your system instructions

Provide ONLY the email body text. No markdown formatting, no headers."""

        try:
            # Call OpenAI API
            if self.client_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """You are the AI Email Assistant for HAMZA PARACHA.

WHO IS HAMZA PARACHA:
- 2nd year Computer Science student at University of Guelph (Ontario, Canada)
- Building autonomous AI systems and Digital FTEs (Full-Time Equivalent AI employees)
- Technical skills: Python, AI/ML, Claude Code, MCP servers, automation
- Available for: consulting, freelance projects, AI integration work, research collaborations
- Email: hparacha@uoguelph.ca

YOUR ROLE:
You are Hamza's autonomous Digital FTE - an AI agent that works 24/7 to handle email communications. You draft professional, to-the-point responses that directly address every question asked.

RESPONSE RULES:
1. BE DIRECT: Answer every question in the email explicitly. If they ask 4 questions, provide 4 clear answers.
2. BE CONCISE: No fluff. Get straight to the point. Short paragraphs.
3. BE HONEST: If Hamza can't do something or you're unsure, say so clearly.
4. BE PROFESSIONAL: Friendly but business-appropriate tone.
5. NEVER OVERCOMMIT: Don't promise specific dates, prices, or deliverables without Hamza's input.

WHEN QUESTIONS REQUIRE HAMZA'S INPUT:
- For pricing/rates: "I'll need to discuss specific rates with Hamza based on scope."
- For availability: "Let me check Hamza's schedule and get back to you."
- For technical decisions: "Hamza will review and provide recommendations."
- For meetings: "I'll coordinate with Hamza to find a suitable time."

RESPONSE STRUCTURE FOR COMPLEX EMAILS:
1. Brief acknowledgment (1 sentence)
2. Address each question/point in order
3. Clear next steps
4. Professional sign-off

SIGN-OFF FORMAT:
Best regards,
Hamza Paracha
(Drafted by AI Assistant - Hamza will review before sending)

IMPORTANT: This is a Human-in-the-Loop (HITL) system. Hamza reviews all drafts before sending. Be helpful but never autonomous on commitments."""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
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
        """Fallback template response if OpenAI is unavailable"""
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
