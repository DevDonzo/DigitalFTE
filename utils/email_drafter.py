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
        self.email_style_path = self.vault / 'EmailStyle.md'
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
            ids = [line.strip() for line in self.processed_emails_file.read_text().strip().split('\n') if line.strip()]
            return set(ids)
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

    def _load_email_style(self) -> str:
        """Load user's personalized email writing style guide"""
        if not self.email_style_path.exists():
            logger.debug("EmailStyle.md not found - using default style")
            return ""

        try:
            content = self.email_style_path.read_text()
            logger.debug("✓ Email style guide loaded")
            return content
        except Exception as e:
            logger.error(f"Error loading email style: {e}")
            return ""

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

        # Extract thread history from body if present
        thread_history = ''
        if '## Thread History' in body:
            thread_section = body.split('## Thread History')[1]
            # Get everything until the next section (##)
            if '## Current Message' in thread_section:
                thread_history = thread_section.split('## Current Message')[0].strip()
            else:
                # If no Current Message section, take until next ## section
                thread_parts = thread_section.split('##')
                if len(thread_parts) > 0:
                    thread_history = '##'.join(thread_parts[:-1]).strip() if len(thread_parts) > 1 else thread_parts[0].strip()

        # Extract current message body (everything after "## Current Message" or last ## section)
        email_body = body
        if '## Current Message' in body:
            email_body = body.split('## Current Message')[1].split('##')[0].strip()
        elif '## Body' in body:
            email_body = body.split('## Body')[1].split('##')[0].strip()

        # Parse thread metadata
        is_reply = metadata.get('is_reply', 'false').lower() == 'true'
        thread_id = metadata.get('thread_id', '')

        # Parse attachments from frontmatter if present
        attachments = []
        if 'attachments:' in frontmatter:
            in_attachments = False
            for line in frontmatter.split('\n'):
                if line.strip() == 'attachments:':
                    in_attachments = True
                elif in_attachments and line.strip().startswith('- '):
                    attachment = line.strip().lstrip('- ').strip()
                    if attachment:
                        attachments.append(attachment)
                elif in_attachments and not line.strip().startswith('- '):
                    break

        return {
            'filename': email_file.name,
            'from': metadata.get('from', 'Unknown'),
            'subject': metadata.get('subject', 'No Subject'),
            'received': metadata.get('received', ''),
            'priority': metadata.get('priority', 'normal'),
            'gmail_message_id': metadata.get('gmail_message_id', ''),
            'thread_id': thread_id,
            'is_reply': is_reply,
            'thread_history': thread_history,
            'attachments': attachments,
            'body': email_body
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

        # Load personalized email style
        email_style = self._load_email_style()
        style_section = ""
        if email_style:
            style_section = f"\n\nPERSONALIZED WRITING STYLE:\n{email_style}\n\nWhen drafting this email, match the tone, style, and voice from the style guide above as closely as possible."

        # Build context-aware prompt based on whether this is a reply
        if email.get('is_reply') and email.get('thread_history'):
            prompt = f"""THREAD CONTEXT (Previous Conversation):

{email['thread_history']}

---

LATEST MESSAGE (Reply to this):
From: {email['from']}
Subject: {email['subject']}

{email['body']}

---

INSTRUCTIONS:
1. Review the ENTIRE thread above for context
2. Reference previous messages naturally where relevant to show continuity
3. Identify EVERY question asked in the latest message (numbered or implied)
4. Address EACH question explicitly in your response
5. For questions requiring Hamza's input (rates, specific dates, commitments), say you'll confirm with Hamza
6. Be direct and to-the-point - no filler phrases
7. Keep response professional but friendly
8. Continue the tone from previous messages in the thread

RESPONSE FORMAT:
- Start with a brief acknowledgment (reference previous context if relevant, 1 sentence max)
- Address each question/point from the latest message
- End with clear next steps
- Use the sign-off format from your system instructions

Provide ONLY the email body text. No markdown formatting, no headers."""
        else:
            # New email (not a reply)
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
                        {"role": "system", "content": f"""You are the AI Email Assistant for HAMZA PARACHA.

WHO IS HAMZA PARACHA:
- 2nd year Software Engineering student at University of Guelph (Ontario, Canada)
- Building autonomous AI systems and Digital FTEs (Full-Time Equivalent AI employees)
- Technical skills: Python, AI/ML, AI Assistant, MCP servers, automation
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

SIGN-OFF FORMAT (Always use this exact format):
Best regards,

Hamza Paracha

---
This message was composed with AI assistance and reviewed by Hamza Paracha before transmission.

IMPORTANT: This is a Human-in-the-Loop (HITL) system. Hamza reviews all drafts before sending. Be helpful but never autonomous on commitments.{style_section}"""},
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

    def _analyze_tone_deviation(self, draft_text: str, email_style: str) -> dict:
        """Compare draft tone against user's style guide"""
        if not self.client or not email_style:
            return {'matches_style': True, 'deviations': [], 'confidence': 1.0}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Compare this draft email against the user's style guide.

STYLE GUIDE:
{email_style}

DRAFT EMAIL:
{draft_text}

Analyze if the draft matches the user's writing style. Return ONLY valid JSON (no markdown, no code blocks):
{{
  "matches_style": true/false,
  "deviations": ["list of specific differences"],
  "confidence": 0.0-1.0
}}

Focus on major deviations only:
- Tone (too formal vs too casual)
- Missing signature elements
- Significant structural differences
- Missing or incorrect closing

Don't flag minor style differences."""
                }],
                temperature=0.3,
                max_tokens=300
            )

            try:
                import json as json_module
                result = json_module.loads(response.choices[0].message.content)
                logger.debug("✓ Tone analysis complete")
                return result
            except json_module.JSONDecodeError:
                logger.debug("Failed to parse tone analysis response as JSON")
                return {'matches_style': True, 'deviations': [], 'confidence': 1.0}

        except Exception as e:
            logger.error(f"Tone analysis error: {e}")
            return {'matches_style': True, 'deviations': [], 'confidence': 1.0}

    def _generate_thread_summary(self, thread_history: str) -> str:
        """Generate AI summary of email thread"""
        if not self.client or not thread_history:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Summarize the key points from this email thread in 3-5 bullet points. Be concise and focus on:
- What has been discussed
- Key decisions or agreements
- What's still pending

THREAD:
{thread_history}

Return ONLY bullet points, no introduction."""
                }],
                temperature=0.5,
                max_tokens=300
            )

            summary = response.choices[0].message.content
            logger.debug("✓ Thread summary generated")
            return summary
        except Exception as e:
            logger.error(f"Thread summary generation error: {e}")
            return ""

    def _create_draft_file(self, email: dict, email_type: str, draft_response: str,
                          confidence: float, auto_approve: bool) -> Path:
        """Create draft approval file in Pending_Approval/ or Approved/ if auto-approve"""

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f"EMAIL_DRAFT_{timestamp}.md"
        # If auto-approved, send directly to Approved folder for immediate sending
        draft_path = self.vault / 'Approved' / draft_filename if auto_approve else self.pending / draft_filename

        # Build thread summary section if this is a reply
        thread_summary_section = ""
        if email.get('is_reply'):
            thread_summary = email.get('thread_summary', '')
            if thread_summary:
                thread_summary_section = f"""
## Thread Summary

Key points from the conversation:

{thread_summary}

---
"""

        # Build tone analysis warnings section if deviations detected
        tone_warning_section = ""
        tone_analysis = email.get('tone_analysis')
        if tone_analysis and (not tone_analysis.get('matches_style', True) or tone_analysis.get('confidence', 1.0) < 0.7):
            deviations = tone_analysis.get('deviations', [])
            confidence = tone_analysis.get('confidence', 0)
            deviation_list = '\n'.join(f'- {d}' for d in deviations) if deviations else '- Style mismatch detected'
            tone_warning_section = f"""
## ⚠️  Style Check Warnings

This draft may not match your typical writing style (confidence: {confidence*100:.0f}%):

{deviation_list}

**Recommendation**: Review carefully or regenerate the draft to better match your style.

---
"""

        # Build draft file content
        draft_content = f"""---
type: email_draft
original_from: {email['from']}
original_subject: {email['subject']}
gmail_message_id: {email.get('gmail_message_id', '')}
thread_id: {email.get('thread_id', '')}
is_reply: {str(email.get('is_reply', False)).lower()}
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

{thread_summary_section}{tone_warning_section}

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

## Attachments

To attach files to this email, add them to the frontmatter at the top of this file:

```yaml
attachments:
  - /Users/hparacha/Downloads/invoice.pdf
  - /Users/hparacha/Desktop/proposal.docx
```

**Supported locations**:
- `~/Downloads`
- `~/Desktop`
- Any absolute file path

**Notes**:
- Files must exist and be accessible
- Gmail limit: 25MB per email
- Common formats: PDF, DOC, XLS, PPT, JPG, PNG, ZIP, CSV

---

## AI-Assisted Composition & Review

This response was composed with advanced AI assistance and has been reviewed by Hamza Paracha prior to transmission.

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
        if email.get('is_reply'):
            logger.debug(f"  This is a reply to a thread (thread_id: {email.get('thread_id')})")

        # Load rules
        handbook_rules = self._load_handbook_rules()

        # Classify email
        email_type, auto_approve = self._classify_email_type(email, handbook_rules)
        logger.debug(f"  Type: {email_type}, Auto-approve: {auto_approve}")

        # Generate draft via AI
        draft_response, confidence = self._generate_draft(email, email_type, handbook_rules)

        # Generate thread summary if this is a reply
        thread_summary = ""
        if email.get('is_reply') and email.get('thread_history'):
            thread_summary = self._generate_thread_summary(email['thread_history'])

        # Add thread summary to email dict for draft file creation
        email['thread_summary'] = thread_summary

        # Analyze tone deviation if EmailStyle.md exists
        email_style = self._load_email_style()
        tone_analysis = None
        if email_style:
            tone_analysis = self._analyze_tone_deviation(draft_response, email_style)

        # Add tone analysis to email dict for draft file creation
        email['tone_analysis'] = tone_analysis

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
        print(f"Example: python email_drafter.py vault/Needs_Action/EMAIL_001.md")
        sys.exit(1)

    email_file = Path(sys.argv[1])

    drafter = EmailDrafter(vault_path)
    result = drafter.draft_reply(email_file)

    if result:
        print(f"✅ Draft created: {result}")
    else:
        print("❌ Failed to create draft")
