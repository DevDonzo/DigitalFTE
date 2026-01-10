"""WhatsApp Business Webhook Server - FastAPI"""
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


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """WhatsApp webhook verification (GET request from Meta)"""
    logger.info(f"Webhook verification: mode={hub_mode}, token={hub_verify_token}")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive incoming WhatsApp messages (POST from Meta)"""
    try:
        payload = await request.json()
        logger.info(f"Webhook received: {json.dumps(payload, indent=2)}")

        # Extract messages from payload
        entry = payload.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        contacts = value.get('contacts', [])

        # Get contact info
        contact_map = {c.get('wa_id'): c.get('profile', {}).get('name', 'Unknown')
                       for c in contacts}

        for msg in messages:
            msg_id = msg.get('id', '')
            sender_id = msg.get('from', '')
            sender_name = contact_map.get(sender_id, sender_id)
            msg_type = msg.get('type', 'text')
            timestamp = msg.get('timestamp', '')

            # Extract text content
            if msg_type == 'text':
                text_content = msg.get('text', {}).get('body', '')
            elif msg_type == 'button':
                text_content = msg.get('button', {}).get('text', '')
            elif msg_type == 'interactive':
                text_content = msg.get('interactive', {}).get('button_reply', {}).get('title', '')
            else:
                text_content = f"[{msg_type} message]"

            logger.info(f"Message from {sender_name} ({sender_id}): {text_content[:100]}")

            # Create action file for orchestrator
            create_whatsapp_action_file(msg_id, sender_id, sender_name, text_content, timestamp)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


def create_whatsapp_action_file(msg_id: str, sender_id: str, sender_name: str,
                                 text: str, timestamp: str):
    """Create a markdown file in Needs_Action for the orchestrator"""
    import hashlib

    # Generate unique filename
    unique_id = hashlib.md5(f"{msg_id}{sender_id}".encode()).hexdigest()[:12]
    filename = f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}.md"
    filepath = NEEDS_ACTION / filename

    # Convert timestamp
    try:
        ts = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
    except:
        ts = datetime.now(timezone.utc).isoformat()

    content = f"""---
type: whatsapp
from: {sender_id}
sender_name: {sender_name}
whatsapp_message_id: {msg_id}
received: {ts}
priority: high
status: pending
---

## From
{sender_name} ({sender_id})

## Message
{text}

## Actions
- [ ] Reply via WhatsApp Business API
- [ ] Forward to email
- [ ] Mark as done
"""

    filepath.write_text(content)
    logger.info(f"Created action file: {filename}")

    # Also store in webhook store for backup
    webhook_store = VAULT_PATH / '.whatsapp_incoming.json'
    try:
        if webhook_store.exists():
            data = json.loads(webhook_store.read_text())
        else:
            data = {'messages': []}

        data['messages'].append({
            'id': msg_id,
            'from': sender_id,
            'sender_name': sender_name,
            'text': {'body': text},
            'timestamp': ts
        })
        webhook_store.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.warning(f"Could not update webhook store: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vault_path": str(VAULT_PATH),
        "verify_token": VERIFY_TOKEN[:5] + "..."
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "DigitalFTE WhatsApp Webhook",
        "endpoints": {
            "/webhook": "WhatsApp webhook (GET for verify, POST for messages)",
            "/health": "Health check"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 8000))
    logger.info(f"Starting WhatsApp webhook server on port {port}")
    logger.info(f"Verify token: {VERIFY_TOKEN}")
    logger.info(f"Vault path: {VAULT_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=port)
