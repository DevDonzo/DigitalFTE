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
        self.model = "gpt-4o-mini"
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✓ WhatsAppDrafter initialized (OpenAI gpt-4o-mini)")
            except ImportError:
                logger.error("OpenAI SDK not installed")
        else:
            logger.warning("OPENAI_API_KEY not set - WhatsApp drafting unavailable")

    def _load_processed(self) -> set:
        if self.processed_file.exists():
            ids = [line.strip() for line in self.processed_file.read_text().strip().split('\n') if line.strip()]
            return set(ids)
        return set()

    def _mark_processed(self, filename: str):
        self.processed_ids.add(filename)
        with open(self.processed_file, 'a') as f:
            f.write(filename + '\n')

    def _generate_reply(self, sender: str, message: str, urgency: str = 'NORMAL') -> tuple:
        """Use OpenAI to generate WhatsApp reply"""
        if not self.client:
            return self._fallback_reply(sender, message), 0.5

        # Load handbook for context
        handbook_context = ""
        if self.handbook.exists():
            handbook_context = self.handbook.read_text()[:2000]

        prompt = f"""Incoming WhatsApp message from: {sender}
Message: {message}

Respond naturally and concisely (WhatsApp style). Address the message directly and helpfully."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """You are the AI WhatsApp Assistant for HAMZA PARACHA.

WHO IS HAMZA PARACHA:
- 2nd year Software Engineering student at University of Guelph (Ontario, Canada)
- Building autonomous AI systems and Digital FTEs (Full-Time Equivalent AI employees)
- Technical skills: Python, AI/ML, AI Assistant, MCP servers, automation
- Available for: consulting, freelance projects, AI integration work, research collaborations

YOUR ROLE:
You are Hamza's autonomous Digital FTE - an AI agent that handles WhatsApp communications 24/7. You respond naturally and helpfully to messages while representing Hamza professionally.

RESPONSE RULES:
1. KEEP IT NATURAL: WhatsApp conversations are casual but professional. Short, friendly messages.
2. BE DIRECT: Answer questions clearly without unnecessary explanation.
3. BE CONCISE: WhatsApp messages should be brief (1-3 sentences per response).
4. BE HONEST: If something requires Hamza's input, say so clearly.
5. NEVER OVERCOMMIT: Don't promise specific dates or deliverables without Hamza's approval.

WHEN QUESTIONS REQUIRE HAMZA'S INPUT:
- For pricing/rates: "I'll need to discuss rates with Hamza based on what you need."
- For availability: "Let me check Hamza's schedule and get back to you."
- For technical decisions: "Hamza will review this and get back to you."

IMPORTANT: You are an AI assistant for Hamza. Be helpful and friendly, but always make it clear you're an AI handling messages on Hamza's behalf."""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()

            # Adjust confidence based on urgency
            # URGENT/BUSINESS messages need human review (lower confidence)
            # INFO messages can be more confident (safe patterns)
            # NORMAL is standard confidence
            if urgency == 'URGENT':
                confidence = 0.65  # Low confidence - needs immediate human review
            elif urgency == 'BUSINESS':
                confidence = 0.70  # Lower confidence - needs careful approval
            elif urgency == 'INFO':
                confidence = 0.92  # High confidence - safe patterns
            else:
                confidence = 0.85  # Standard confidence

            return reply, confidence
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._fallback_reply(sender, message), 0.5

    def _fallback_reply(self, sender: str, message: str) -> str:
        """Template reply when OpenAI unavailable"""
        return f"""Hi {sender},

Thanks for your message. I'm Hamza's AI assistant and I've received it. I'll get back to you shortly.

Best regards,
Hamza's AI Assistant"""

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
            urgency = "NORMAL"  # Default urgency
            priority = "NORMAL"  # Default priority

            # Extract frontmatter for urgency
            if content.startswith("---"):
                frontmatter_end = content.find("---", 3)
                if frontmatter_end > 0:
                    frontmatter = content[:frontmatter_end]
                    for line in frontmatter.split('\n'):
                        if line.startswith('urgency:'):
                            urgency = line.split(':', 1)[1].strip()
                        elif line.startswith('priority:'):
                            priority = line.split(':', 1)[1].strip()
                        elif line.startswith('from:'):
                            sender = line.split(':', 1)[1].strip()

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
            reply_text, confidence = self._generate_reply(sender, message, urgency)

            # Create draft file
            draft_file = self._create_draft_file(sender, message, reply_text, confidence, filename, urgency)

            self._mark_processed(filename)
            return draft_file

        except Exception as e:
            logger.error(f"Error drafting WhatsApp reply: {e}")
            return None

    def _create_draft_file(self, sender: str, original_msg: str, reply: str, confidence: float, original_file: str, urgency: str = 'NORMAL') -> Path:
        """Create draft reply file in Pending_Approval"""
        self.pending.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f"WHATSAPP_DRAFT_{timestamp}.md"

        # Urgency indicators
        urgency_indicator = {
            'URGENT': '🔴',
            'BUSINESS': '🟠',
            'INFO': '🟢',
            'NORMAL': '⚪'
        }.get(urgency, '⚪')

        # Add note about urgency/confidence
        urgency_note = ""
        if urgency == 'URGENT':
            urgency_note = "\n⚠️ **URGENT MESSAGE** - Requires immediate review"
        elif urgency == 'BUSINESS':
            urgency_note = "\n⚠️ **BUSINESS MESSAGE** - Requires careful approval (pricing, contracts, etc)"
        elif urgency == 'INFO':
            urgency_note = "\n✓ **INFO MESSAGE** - Low risk, high confidence in auto-response"

        content = f"""---
type: whatsapp_draft
original_file: {original_file}
to: {sender}
created: {datetime.now().isoformat()}
ai_generated: true
confidence: {confidence}
urgency: {urgency}
status: pending_approval
---

## Original Message

**From:** {sender}
**Urgency:** {urgency_indicator} {urgency}{urgency_note}

{original_msg}

## Proposed Reply

{reply}

## Actions

- [ ] Edit reply above if needed
- [ ] Move to /Approved/ to send
- [ ] Delete to discard

*AI-generated draft. Confidence: {confidence:.0%} | Review before sending.*
"""
        draft_path = self.pending / draft_filename
        draft_path.write_text(content)
        logger.info(f"✓ WhatsApp draft created: {draft_filename} [{urgency_indicator} {urgency}, confidence: {confidence:.0%}]")
        return draft_path
