"""WhatsApp Drafter - OpenAI-powered autonomous response generation"""
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


class WhatsAppDrafter:
    """Uses OpenAI API to intelligently draft WhatsApp responses"""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'
        self.needs_action = self.vault / 'Needs_Action'
        self.pending = self.vault / 'Pending_Approval'
        self.handbook = self.vault / 'Company_Handbook.md'
        self.processed_file = self.vault / '.processed_whatsapp'
        self.processed_ids = self._load_processed()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✓ WhatsAppDrafter initialized (OpenAI gpt-3.5-turbo)")
            except ImportError:
                logger.error("OpenAI SDK not installed")
        else:
            logger.warning("OPENAI_API_KEY not set - WhatsApp drafting unavailable")

    def _load_processed(self) -> set:
        if self.processed_file.exists():
            return set(self.processed_file.read_text().strip().split('\n'))
        return set()

    def _mark_processed(self, filename: str):
        self.processed_ids.add(filename)
        with open(self.processed_file, 'a') as f:
            f.write(filename + '\n')

    def _generate_reply(self, sender: str, message: str) -> tuple:
        """Use OpenAI to generate WhatsApp reply"""
        if not self.client:
            return self._fallback_reply(sender, message), 0.5

        # Load handbook for context
        handbook_context = ""
        if self.handbook.exists():
            handbook_context = self.handbook.read_text()[:2000]

        prompt = f"""You are an AI assistant helping draft WhatsApp message replies.

Context from Company Handbook:
{handbook_context}

---

Incoming WhatsApp message from: {sender}
Message: {message}

---

Draft a helpful, professional but friendly reply. Keep it concise (WhatsApp style - not too formal).
If the message requires action (payment, meeting, etc.), acknowledge it and state what you'll do.
Keep response under 200 words.

Reply:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            confidence = 0.85
            return reply, confidence
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._fallback_reply(sender, message), 0.5

    def _fallback_reply(self, sender: str, message: str) -> str:
        """Template reply when OpenAI unavailable"""
        return f"""Hi {sender},

Thanks for your message. I've received it and will get back to you shortly.

Best regards"""

    def draft_reply(self, whatsapp_file: Path) -> Optional[Path]:
        """Main entry: Draft a reply for a WhatsApp message file"""
        if not whatsapp_file.exists():
            return None

        filename = whatsapp_file.name
        if filename in self.processed_ids:
            logger.debug(f"Already processed: {filename}")
            return None

        try:
            content = whatsapp_file.read_text()

            # Parse the WhatsApp file
            sender = "Unknown"
            message = ""
            full_context = ""

            for line in content.split('\n'):
                if line.startswith('from:'):
                    sender = line.split(':', 1)[1].strip()
                elif line.startswith('## From'):
                    # Next non-empty line is sender
                    continue
                elif line.startswith('## Message'):
                    continue
                elif line.startswith('## Full Context'):
                    continue

            # Extract message section
            if '## Message' in content:
                msg_section = content.split('## Message')[1]
                if '## Full Context' in msg_section:
                    message = msg_section.split('## Full Context')[0].strip()
                elif '## Actions' in msg_section:
                    message = msg_section.split('## Actions')[0].strip()
                else:
                    message = msg_section.strip()

            # Extract full context
            if '## Full Context' in content:
                ctx_section = content.split('## Full Context')[1]
                if '## Actions' in ctx_section:
                    full_context = ctx_section.split('## Actions')[0].strip()
                else:
                    full_context = ctx_section.strip()

            # Use full context if message is truncated
            if len(message) < 50 and full_context:
                message = full_context

            if not message:
                logger.warning(f"No message content in {filename}")
                return None

            # Generate reply
            reply_text, confidence = self._generate_reply(sender, message)

            # Create draft file
            draft_file = self._create_draft_file(sender, message, reply_text, confidence, filename)

            self._mark_processed(filename)
            return draft_file

        except Exception as e:
            logger.error(f"Error drafting WhatsApp reply: {e}")
            return None

    def _create_draft_file(self, sender: str, original_msg: str, reply: str, confidence: float, original_file: str) -> Path:
        """Create draft reply file in Pending_Approval"""
        self.pending.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f"WHATSAPP_DRAFT_{timestamp}.md"

        content = f"""---
type: whatsapp_draft
original_file: {original_file}
to: {sender}
created: {datetime.now().isoformat()}
ai_generated: true
confidence: {confidence}
status: pending_approval
---

## Original Message

**From:** {sender}

{original_msg}

---

## Proposed Reply

{reply}

---

## Actions

- [ ] Edit reply above if needed
- [ ] Move to /Approved/ to send
- [ ] Delete to discard

---

*AI-generated draft. Review before sending.*
"""
        draft_path = self.pending / draft_filename
        draft_path.write_text(content)
        logger.info(f"✓ WhatsApp draft created: {draft_filename}")
        return draft_path
