# WhatsApp Monitor Agent Skill

**Skill ID**: `whatsapp-monitor`
**Type**: Watcher / Monitoring
**Tier**: Silver
**Dependencies**: Playwright, WhatsApp Web

## Purpose

Monitor incoming WhatsApp messages for keywords and create action files for important communications.

## Capabilities

- Monitor unread WhatsApp messages in real-time
- Filter messages by keywords (urgent, asap, invoice, payment, help, etc.)
- Create markdown action files in vault for keyword-matching messages
- Track message metadata (sender, timestamp, content)
- Graceful error handling for login/authentication issues

## Usage

```bash
python watchers/whatsapp_watcher.py
```

## Configuration

Set in `.env`:
```
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session  # Persistent browser session
WHATSAPP_CHECK_INTERVAL=30                        # Check every 30 seconds
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help  # Keywords to monitor
```

## Technical Implementation

Uses Playwright for WhatsApp Web automation:
- Maintains persistent browser session for faster checks
- Selects unread chats with aria-labels
- Filters by keyword matches
- Creates markdown files in `vault/Inbox/`

## File Output Format

Creates files like `vault/Inbox/WHATSAPP_20260108_143022.md`:
```markdown
---
type: whatsapp
from: John Smith
received: 2026-01-08T14:30:22Z
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

- **Orchestrator**: Reads from `vault/Inbox/WHATSAPP_*.md`
- **Approval**: Human reviews in `Pending_Approval/`
- **Action**: Triggers email replies or forwarding

## Error Handling

- Catches playwright errors gracefully
- Logs all errors to audit trail
- Continues monitoring on failure
- Maintains processed message tracking
