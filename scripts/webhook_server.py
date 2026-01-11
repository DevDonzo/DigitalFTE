"""WhatsApp Webhook Server - FastAPI (supports Twilio and Meta)"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="DigitalFTE WhatsApp Webhook")

# Config
VAULT_PATH = Path(os.getenv('VAULT_PATH', './vault'))
VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'digitalfte_verify')
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

# Keyword classifications for message urgency
URGENT_KEYWORDS = ['urgent', 'asap', 'emergency', 'help', 'problem', 'crisis', 'down', 'broken', 'critical', 'immediately']
BUSINESS_KEYWORDS = ['pricing', 'rate', 'invoice', 'payment', 'contract', 'proposal', 'quote', 'budget', 'cost', 'fee']
INFO_KEYWORDS = ['thanks', 'ok', 'yes', 'no', 'sounds', 'great', 'perfect', 'confirmed', 'received']

# Track processed message IDs to prevent duplicates
PROCESSED_FILE = VAULT_PATH / '.processed_twilio_messages'
def _load_processed_messages():
    """Load processed message IDs from file, filtering empty strings"""
    if PROCESSED_FILE.exists():
        ids = [line.strip() for line in PROCESSED_FILE.read_text().strip().split('\n') if line.strip()]
        return set(ids)
    return set()

PROCESSED_MESSAGES = _load_processed_messages()


def classify_urgency(message_text: str) -> str:
    """Classify message urgency based on keywords"""
    text_lower = message_text.lower()

    # Check for urgent keywords first
    for keyword in URGENT_KEYWORDS:
        if keyword in text_lower:
            return 'URGENT'

    # Check for business keywords
    for keyword in BUSINESS_KEYWORDS:
        if keyword in text_lower:
            return 'BUSINESS'

    # Check for info keywords
    for keyword in INFO_KEYWORDS:
        if keyword in text_lower:
            return 'INFO'

    # Default to NORMAL
    return 'NORMAL'


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Webhook verification (GET from Meta)"""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✓ Webhook verified")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("✗ Verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive WhatsApp messages from Twilio or Meta"""
    try:
        content_type = request.headers.get("content-type", "")

        if "application/x-www-form-urlencoded" in content_type:
            # Twilio webhook
            form_data = await request.form()
            await handle_twilio_webhook(form_data)
            return PlainTextResponse("")
        else:
            # Meta webhook
            payload = await request.json()
            await handle_meta_webhook(payload)
            return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}


async def handle_twilio_webhook(form_data):
    """Handle Twilio WhatsApp webhook"""
    # Only process incoming messages, not status updates
    message_status = form_data.get("MessageStatus", "")
    message_text = form_data.get("Body", "")
    msg_id = form_data.get("MessageSid", "")

    # Only process if it's an incoming message (has Body) and not a status callback
    if not message_text:
        logger.debug(f"Ignoring status callback: {message_status}")
        return

    # Skip if no message ID
    if not msg_id:
        logger.warning("No MessageSid found in webhook")
        return

    # Skip if already processed (deduplicate)
    if msg_id in PROCESSED_MESSAGES:
        logger.info(f"⏭️ Duplicate message skipped: {msg_id}")
        return

    from_number = form_data.get("From", "").replace("whatsapp:", "")

    logger.info(f"📱 Incoming message from {from_number}: {message_text[:50]}")
    logger.debug(f"Message ID: {msg_id}")

    # Mark as processed BEFORE creating file (prevent race condition)
    PROCESSED_MESSAGES.add(msg_id)
    with open(PROCESSED_FILE, 'a') as f:
        f.write(msg_id + '\n')

    logger.info(f"✓ Message {msg_id} marked as processed")
    urgency = classify_urgency(message_text)
    create_whatsapp_action_file(msg_id, from_number, from_number, message_text, "", urgency)


async def handle_meta_webhook(payload):
    """Handle Meta WhatsApp webhook"""
    logger.info(f"📱 Meta WhatsApp webhook received")

    entry = payload.get('entry', [{}])[0]
    changes = entry.get('changes', [{}])[0]
    value = changes.get('value', {})
    messages = value.get('messages', [])
    contacts = value.get('contacts', [])

    contact_map = {c.get('wa_id'): c.get('profile', {}).get('name', 'Unknown')
                   for c in contacts}

    for msg in messages:
        msg_id = msg.get('id', '')
        sender_id = msg.get('from', '')
        sender_name = contact_map.get(sender_id, sender_id)
        msg_type = msg.get('type', 'text')

        if msg_type == 'text':
            text_content = msg.get('text', {}).get('body', '')
        elif msg_type == 'button':
            text_content = msg.get('button', {}).get('text', '')
        elif msg_type == 'interactive':
            text_content = msg.get('interactive', {}).get('button_reply', {}).get('title', '')
        else:
            text_content = f"[{msg_type} message]"

        # Skip if already processed (deduplicate)
        if msg_id in PROCESSED_MESSAGES:
            logger.info(f"⏭️ Duplicate message skipped: {msg_id}")
            continue

        logger.info(f"Message from {sender_name} ({sender_id}): {text_content[:50]}")

        # Mark as processed
        PROCESSED_MESSAGES.add(msg_id)
        with open(PROCESSED_FILE, 'a') as f:
            f.write(msg_id + '\n')

        urgency = classify_urgency(text_content)
        create_whatsapp_action_file(msg_id, sender_id, sender_name, text_content, "", urgency)


def create_whatsapp_action_file(msg_id: str, sender_id: str, sender_name: str,
                                text: str, timestamp: str, urgency: str = 'NORMAL'):
    """Create markdown file in Needs_Action for orchestrator"""
    import hashlib

    unique_id = hashlib.md5(f"{msg_id}{sender_id}".encode()).hexdigest()[:12]
    filename = f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}.md"
    filepath = NEEDS_ACTION / filename

    # Add urgency indicator to filename for easier sorting
    urgency_indicator = {
        'URGENT': '🔴',
        'BUSINESS': '🟠',
        'INFO': '🟢',
        'NORMAL': '⚪'
    }.get(urgency, '⚪')

    content = f"""---
type: whatsapp_message
from: {sender_id}
from_name: {sender_name}
received: {datetime.now().isoformat()}
message_id: {msg_id}
urgency: {urgency}
priority: {'HIGH' if urgency == 'URGENT' else 'MEDIUM' if urgency in ['BUSINESS', 'INFO'] else 'NORMAL'}
---

## WhatsApp Message

**From**: {sender_name} ({sender_id})
**Time**: {datetime.now().isoformat()}
**Urgency**: {urgency_indicator} {urgency}

## Message

{text}

## Actions

- [ ] Draft reply
- [ ] Approve and send
"""

    filepath.write_text(content)
    logger.info(f"✓ Created: {filename} [{urgency_indicator} {urgency}]")


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "DigitalFTE WhatsApp Webhook"}


if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 8001))
    logger.info(f"🚀 Starting webhook server on port {port}")
    logger.info(f"   Webhook URL: http://localhost:{port}/webhook")
    uvicorn.run(app, host="0.0.0.0", port=port)
