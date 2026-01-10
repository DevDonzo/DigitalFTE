"""WhatsApp Watcher - WhatsApp Business Cloud API integration"""
import os
import json
import logging
import requests
import hashlib
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
    """WhatsApp Business Cloud API watcher and sender"""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, vault_path: str, session_path: str = None):
        super().__init__(vault_path, check_interval=30)

        # WhatsApp Business API credentials
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN') or os.getenv('META_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'digitalfte_verify')

        # Processed messages tracking
        self.processed_file = Path(vault_path) / '.processed_whatsapp_messages'
        self.processed_ids = self._load_processed()

        if not self.access_token:
            logger.warning("WHATSAPP_ACCESS_TOKEN not set - WhatsApp Business API unavailable")
        if not self.phone_number_id:
            logger.warning("WHATSAPP_PHONE_NUMBER_ID not set")

        if self.access_token and self.phone_number_id:
            logger.info("✓ WhatsApp Business Cloud API initialized")

    def _load_processed(self) -> set:
        """Load processed message IDs"""
        if self.processed_file.exists():
            return set(self.processed_file.read_text().strip().split('\n'))
        return set()

    def _mark_processed(self, msg_id: str):
        """Mark message as processed"""
        self.processed_ids.add(msg_id)
        with open(self.processed_file, 'a') as f:
            f.write(msg_id + '\n')

    def check_for_updates(self) -> list:
        """Check for new WhatsApp messages via Business API"""
        messages = []

        if not self.access_token or not self.phone_number_id:
            logger.debug("WhatsApp Business API not configured")
            return messages

        # Note: WhatsApp Business API uses webhooks for incoming messages
        # This method checks the webhook endpoint for any stored messages
        # In production, you'd have a webhook server storing incoming messages

        webhook_store = Path(self.vault_path) / '.whatsapp_incoming.json'

        if webhook_store.exists():
            try:
                incoming = json.loads(webhook_store.read_text())
                for msg in incoming.get('messages', []):
                    msg_id = msg.get('id', '')
                    if msg_id and msg_id not in self.processed_ids:
                        messages.append(msg)
                        logger.info(f"New WhatsApp message from {msg.get('from', 'unknown')}")

                # Clear processed messages from store
                if messages:
                    remaining = [m for m in incoming.get('messages', [])
                                if m.get('id') not in self.processed_ids]
                    incoming['messages'] = remaining
                    webhook_store.write_text(json.dumps(incoming))

            except Exception as e:
                logger.error(f"Error reading webhook store: {e}")

        return messages

    def send_message(self, to_phone: str, message: str) -> dict:
        """Send WhatsApp message via Business Cloud API"""
        if not self.access_token or not self.phone_number_id:
            raise RuntimeError("WhatsApp Business API not configured")

        # Normalize phone number (remove spaces, dashes, ensure + prefix)
        to_phone = to_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not to_phone.startswith('+'):
            to_phone = '+' + to_phone
        to_phone = to_phone.replace('+', '')  # API needs number without +

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            message_id = result.get('messages', [{}])[0].get('id')
            logger.info(f"✅ WhatsApp message sent to {to_phone}")
            logger.info(f"   Message ID: {message_id}")

            # Log the sent message
            log_file = Path(self.vault_path) / 'Logs' / 'whatsapp_sent.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                'to': to_phone,
                'message': message[:200] + '...' if len(message) > 200 else message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'sent',
                'message_id': message_id
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            return result

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"WhatsApp API error: {e.response.status_code} - {error_detail}")
            raise RuntimeError(f"WhatsApp API error: {error_detail}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    def send_template_message(self, to_phone: str, template_name: str,
                              language_code: str = "en", components: list = None) -> dict:
        """Send WhatsApp template message (for business-initiated conversations)"""
        if not self.access_token or not self.phone_number_id:
            raise RuntimeError("WhatsApp Business API not configured")

        to_phone = to_phone.replace(' ', '').replace('-', '').replace('+', '')

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }

        if components:
            payload["template"]["components"] = components

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ WhatsApp template message sent to {to_phone}")
            return result
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            raise

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        if not self.access_token or not self.phone_number_id:
            return False

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.debug(f"Marked message {message_id} as read")
            return True
        except Exception as e:
            logger.warning(f"Could not mark message as read: {e}")
            return False

    def create_action_file(self, item) -> Path:
        """Create markdown file for WhatsApp message"""
        try:
            sender = item.get('from', 'Unknown')
            msg_id = item.get('id', '')
            text_content = item.get('text', {}).get('body', '') if isinstance(item.get('text'), dict) else str(item.get('text', ''))
            timestamp = item.get('timestamp', datetime.now().isoformat())

            content = f"""---
type: whatsapp
from: {sender}
whatsapp_message_id: {msg_id}
received: {timestamp}
priority: high
status: pending
---

## From
{sender}

## Message
{text_content}

## Actions
- [ ] Reply via WhatsApp Business API
- [ ] Forward to email
- [ ] Mark as done
"""
            unique_id = hashlib.md5(f"{msg_id}{sender}".encode()).hexdigest()[:12]
            filepath = self.inbox / f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}.md"
            filepath.write_text(content)

            # Mark as processed
            if msg_id:
                self._mark_processed(msg_id)

            logger.info(f"Created: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return None


# Webhook handler for incoming messages (for use with Flask/FastAPI)
def handle_webhook_verification(request_args: dict, verify_token: str) -> tuple:
    """Handle WhatsApp webhook verification (GET request)"""
    mode = request_args.get('hub.mode')
    token = request_args.get('hub.verify_token')
    challenge = request_args.get('hub.challenge')

    if mode == 'subscribe' and token == verify_token:
        logger.info("Webhook verified successfully")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed")
        return "Forbidden", 403


def handle_webhook_event(payload: dict, vault_path: str) -> bool:
    """Handle incoming WhatsApp webhook event (POST request)"""
    try:
        webhook_store = Path(vault_path) / '.whatsapp_incoming.json'

        # Load existing messages
        if webhook_store.exists():
            existing = json.loads(webhook_store.read_text())
        else:
            existing = {'messages': []}

        # Extract messages from webhook payload
        entry = payload.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])

        for msg in messages:
            msg['timestamp'] = datetime.now(timezone.utc).isoformat()
            existing['messages'].append(msg)
            logger.info(f"Received WhatsApp message from {msg.get('from')}")

        # Save updated messages
        webhook_store.write_text(json.dumps(existing, indent=2))
        return True

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return False


if __name__ == '__main__':
    vault_path = os.getenv('VAULT_PATH', './vault')
    watcher = WhatsAppWatcher(vault_path)

    # Test sending a message
    if len(os.sys.argv) > 2:
        to_phone = os.sys.argv[1]
        message = os.sys.argv[2]
        result = watcher.send_message(to_phone, message)
        print(f"Result: {result}")
    else:
        # Run watcher
        watcher.run()
