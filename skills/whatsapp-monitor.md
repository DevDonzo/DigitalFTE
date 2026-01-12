# WhatsApp Monitor Agent Skill

**Skill ID**: `whatsapp-monitor`
**Type**: Watcher / Monitoring
**Tier**: Silver
**Dependencies**: Twilio WhatsApp, FastAPI webhook

## Purpose

Monitor incoming WhatsApp messages from a Twilio webhook and create action files for important communications.

## Capabilities

- Monitor unread WhatsApp messages in real-time
- Filter messages by keywords (urgent, asap, invoice, payment, help, etc.)
- Create markdown action files in vault for keyword-matching messages
- Track message metadata (sender, timestamp, content)
- Graceful error handling for login/authentication issues

## Usage

```bash
python scripts/webhook_server.py
python watchers/whatsapp_watcher.py
```

## Configuration

Set in `.env`:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+1234567890
WHATSAPP_CHECK_INTERVAL=30                        # Check every 30 seconds
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help  # Keywords to monitor
```

## Technical Implementation

Uses Twilio webhook ingestion:
- Webhook server stores inbound messages in `.whatsapp_incoming.json`
- Watcher filters by keyword matches
- Creates markdown files in `vault/Needs_Action/`

## File Output Format

Creates files like `vault/Needs_Action/WHATSAPP_20260108_143022.md`:
```markdown
---
type: whatsapp
from: John Smith
received: 2026-01-08T14:30:22Z
urgency: BUSINESS
priority: high
status: pending
---

## Message
Invoice #12345 needs payment ASAP!

## Actions
- [ ] Reply
- [ ] Forward to email
- [ ] Mark as done
```

## Integration Points

- **Orchestrator**: Reads from `vault/Needs_Action/WHATSAPP_*.md`
- **Approval**: Human reviews in `Pending_Approval/`
- **Action**: Triggers email replies or forwarding

## Error Handling

- Catches webhook and queue errors gracefully
- Logs all errors to audit trail
- Continues monitoring on failure
- Maintains processed message tracking
