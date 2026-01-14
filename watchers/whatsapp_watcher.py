"""WhatsApp Watcher - Twilio WhatsApp API integration"""
import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
try:
    from .base_watcher import BaseWatcher
except ImportError:
    from base_watcher import BaseWatcher

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppWatcher(BaseWatcher):
    """Twilio WhatsApp API watcher and sender"""

    def __init__(self, vault_path: str, session_path: str = None):
        super().__init__(vault_path, check_interval=10)

        # Twilio WhatsApp credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

        # Processed messages tracking
        self.processed_file = Path(vault_path) / '.processed_whatsapp_messages'
        self.processed_ids = self._load_processed()

        if not self.account_sid or not self.auth_token:
            logger.warning("⚠️ TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set")
        elif not self.whatsapp_number:
            logger.warning("⚠️ TWILIO_WHATSAPP_NUMBER not set")
        else:
            logger.info(f"✓ Twilio WhatsApp initialized ({self.whatsapp_number})")

    def _load_processed(self) -> set:
        """Load processed message IDs"""
        if self.processed_file.exists():
            ids = [line.strip() for line in self.processed_file.read_text().strip().split('\n') if line.strip()]
            return set(ids)
        return set()

    def _mark_processed(self, msg_id: str):
        """Mark message as processed"""
        self.processed_ids.add(msg_id)
        with open(self.processed_file, 'a') as f:
            f.write(msg_id + '\n')

    def check_for_updates(self) -> list:
        """Check for new WhatsApp messages via webhook storage"""
        messages = []

        # Incoming messages are stored by webhook
        webhook_store = Path(self.vault_path) / '.whatsapp_incoming.json'

        if webhook_store.exists():
            try:
                incoming = json.loads(webhook_store.read_text())
                remaining = []
                for msg in incoming.get('messages', []):
                    msg_id = msg.get('id', '')
                    if msg_id not in self.processed_ids:
                        messages.append(msg)
                        self._mark_processed(msg_id)
                    else:
                        remaining.append(msg)
                if remaining:
                    webhook_store.write_text(json.dumps({'messages': remaining}, indent=2))
                else:
                    webhook_store.unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"Error reading webhook store: {e}")

        return messages

    def create_action_file(self, message: dict) -> Path:
        """Create action file for incoming WhatsApp message"""
        msg_id = message.get('id', 'unknown')
        from_number = message.get('from', 'unknown')
        text = message.get('text', {}).get('body', 'No text') if isinstance(message.get('text'), dict) else message.get('text', 'No text')
        timestamp = datetime.now().isoformat()
        urgency = message.get('urgency', 'NORMAL')

        content = f"""---
type: whatsapp_message
from: {from_number}
received: {timestamp}
message_id: {msg_id}
platform: twilio
urgency: {urgency}
---

## WhatsApp Message

**From**: {from_number}
**Received**: {timestamp}

## Message Content

{text}

## Actions

- [ ] Draft reply
- [ ] Send response
"""

        # Save to Needs_Action
        filename = f"WHATSAPP_{timestamp.replace(':', '').replace('-', '')}_twilio.md"
        filepath = self.needs_action / filename

        filepath.write_text(content)
        logger.info(f"✓ Created action file: {filename}")
        
        # Log the incoming message
        self._log_incoming_message(msg_id, from_number, text, urgency, timestamp)

        return filepath
    
    def _log_incoming_message(self, msg_id: str, from_number: str, text: str, urgency: str, timestamp: str):
        """Log incoming WhatsApp message to audit trail"""
        log_file = Path(self.vault_path) / 'Logs' / 'whatsapp_received.jsonl'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            'message_id': msg_id,
            'from': from_number,
            'text': text[:200] + '...' if len(text) > 200 else text,
            'timestamp': timestamp,
            'urgency': urgency,
            'status': 'received',
            'platform': 'twilio'
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info(f"✓ Logged incoming WhatsApp: {msg_id} from {from_number}")

    def send_message(self, to_phone: str, message: str) -> dict:
        """Send WhatsApp message via Twilio"""
        if not self.account_sid or not self.auth_token or not self.whatsapp_number:
            raise RuntimeError("Twilio WhatsApp not configured")

        # Normalize phone number
        to_phone = to_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not to_phone.startswith('+'):
            to_phone = '+' + to_phone

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        payload = {
            "From": f"whatsapp:{self.whatsapp_number}",
            "To": f"whatsapp:{to_phone}",
            "Body": message
        }

        try:
            response = requests.post(
                url,
                data=payload,
                auth=(self.account_sid, self.auth_token)
            )
            response.raise_for_status()
            result = response.json()

            message_id = result.get('sid')
            logger.info(f"✅ WhatsApp sent to {to_phone}")
            logger.info(f"   SID: {message_id}")

            # Log the sent message
            log_file = Path(self.vault_path) / 'Logs' / 'whatsapp_sent.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                'to': to_phone,
                'message': message[:200] + '...' if len(message) > 200 else message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'sent',
                'message_id': message_id,
                'platform': 'twilio'
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            return result

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    def run(self):
        """Run the watcher"""
        logger.info(f"Starting Twilio WhatsApp Watcher (checking every {self.check_interval}s)")
        while True:
            try:
                messages = self.check_for_updates()
                for msg in messages:
                    self.create_action_file(msg)
            except Exception as e:
                logger.error(f"Watcher error: {e}")

            import time
            time.sleep(self.check_interval)


if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    watcher = WhatsAppWatcher(vault_path)
    watcher.run()
