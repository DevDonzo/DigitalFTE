# Email Drafting System

## Overview

The email drafting system intelligently generates responses to incoming emails using OpenAI's language model. Email analysis and response generation is performed with human-in-the-loop approval before sending.

---

## Architecture

### Process Flow

```
Email Received (Gmail)
    |
    v
Gmail Watcher Detection
    |
    v
vault/Needs_Action/EMAIL_*.md
    |
    v
Orchestrator Detection
    |
    v
EmailDrafter Analysis
    |
    +-- Parse email content
    +-- Load Company_Handbook rules
    +-- Classify email type
    +-- Call OpenAI (gpt-4o-mini)
    |
    v
vault/Pending_Approval/EMAIL_DRAFT_*.md
    |
    v
Human Review (Obsidian)
    |
    +-- Edit if needed
    +-- Move to Approved/
    |
    v
vault/Approved/
    |
    v
Email MCP → Gmail API → Recipient
    |
    v
vault/Done/
    |
    v
vault/Logs/ (audit entry)
```

---

## Components

### EmailDrafter Module (utils/email_drafter.py)

Processes incoming emails and generates AI responses:

**Initialization**:
- Loads OpenAI API key
- Initializes model: `gpt-4o-mini`
- Tracks processed emails (deduplication)

**Key Methods**:

- `draft_reply(email_file)` - Main entry point
  - Input: Markdown file from `vault/Needs_Action/`
  - Output: Draft file in `vault/Pending_Approval/`
  - Handles: Parsing, API calls, file creation

- `_parse_email(content)` - Extract email metadata
  - Extracts: From, To, Subject, Body, Headers
  - Returns: Structured email data

- `_classify_email_type(subject, body)` - Determine intent
  - Returns: meeting_request, invoice, complaint, inquiry, general

- `_generate_draft(sender, content)` - Call OpenAI
  - System prompt: Defines tone and rules
  - Max tokens: 500
  - Temperature: 0.7

**System Prompt**:
```
You are an email assistant. Analyze the email and generate a professional response.
- Keep responses concise (<200 words)
- Be friendly but professional
- If uncertain, ask clarifying questions
- Flag urgent items for human review
```

**Confidence Scoring**:
- 0.85-0.95: High confidence (standard emails)
- 0.70-0.84: Medium confidence (requires review)
- 0.50-0.69: Low confidence (needs human input)

Confidence stored in draft frontmatter; visible to human reviewer.

### Orchestrator Integration (scripts/orchestrator.py)

Orchestrator detects new emails and calls drafter:

**On Startup**:
```python
self.email_drafter = EmailDrafter(vault_path)
```

**On File Detection**:
```python
if is_email and self.email_drafter:
    draft_file = self.email_drafter.draft_reply(filepath)
    if draft_file:
        logger.info(f"Email draft created: {draft_file.name}")
```

**Execution**:
```python
if 'EMAIL' in filepath.name:
    self._execute_email(filepath, content)  # Sends via Gmail API
```

### Automation Rules (vault/Company_Handbook.md)

Defines email handling policies:

**Format**:
```yaml
---
type: company_handbook
version: 1.0
---

# Email Response Rules

## Priority Contacts
List of senders whose emails require immediate attention

## Auto-Approval Rules
- Types of emails that can be auto-approved
- Confidence thresholds
- Financial limits (if applicable)

## Tone Guidelines
- Professional vs. casual contexts
- Signature requirements
- Escalation procedures

## Special Handling
- Complaint resolution procedure
- Sensitive topic handling
- External party communications
```

### Email Draft Format

Drafts created in `vault/Pending_Approval/`:

```markdown
---
type: email_draft
original_file: EMAIL_client_20260111_120000.md
to: client@example.com
subject: Re: Project Update
created: 2026-01-11T12:00:15
ai_generated: true
confidence: 0.85
status: pending_approval
---

## Original Email

**From:** client@example.com
**Subject:** Project Update
**Received:** 2026-01-11T12:00:00

Hi,

Can you provide an update on the project timeline?

Thanks,
Client

## Email Analysis

**Type:** Inquiry
**Urgency:** Standard
**Suggested Response:** Provide factual update on timeline

## Proposed Reply

Hi Client,

Thanks for checking in on the project. Here's the current status:

- Phase 1: Complete
- Phase 2: In progress (ETA Friday)
- Phase 3: Scheduled to start Monday

I'll send a detailed report by end of week.

Best regards,
Hamza

## Actions

- [ ] Edit reply above if needed
- [ ] Move to /Approved/ to send
- [ ] Delete to discard

*AI-generated draft. Confidence: 85% | Review before sending.*
```

---

## Data Flow

### Input: Email in Inbox

File format: `vault/Needs_Action/EMAIL_<sender>_<timestamp>.md`

```markdown
---
type: email
from: client@example.com
to: hamza@example.com
subject: Project Update
received: 2026-01-11T12:00:00
message_id: msg_abc123
---

## Email

Hi,

Can you provide an update on the project timeline?

Thanks,
Client
```

### Processing: Drafter Analysis

1. Parse email metadata
2. Extract subject and body
3. Load Company_Handbook rules
4. Classify email type
5. Call OpenAI API with:
   - System prompt (with rules)
   - Email content
   - Context (sender, type, company info)
6. Receive AI-generated response
7. Calculate confidence score
8. Create draft file

### Output: Draft in Pending_Approval

File format: `vault/Pending_Approval/EMAIL_DRAFT_<timestamp>.md`

Contains:
- Original email (full quote)
- Drafter analysis (intent, urgency, type)
- Proposed response (AI-generated)
- Confidence score (for prioritization)
- Meta information (timestamps, file IDs)

---

## Configuration

### Environment Variables

```bash
# OpenAI API
OPENAI_API_KEY=sk-xxx

# Email processing
COMPANY_HANDBOOK_PATH=./vault/Company_Handbook.md
VAULT_PATH=./vault
```

### Handbook Rules

Edit `vault/Company_Handbook.md` to customize:

```yaml
# Adjust for your organization
auto_approve_contacts:
  - boss@company.com
  - team@company.com

min_confidence_for_approval: 0.8

response_templates:
  greeting: "Hi {sender_name},"
  closing: "Best regards,\nTeam"
```

---

## Usage Workflow

### For Users

1. **Email Arrives** → Gmail Watcher detects (within 20s)
2. **Draft Created** → Appears in `vault/Pending_Approval/`
3. **Review** → Open in Obsidian
   - Read original email
   - Check AI analysis
   - Review proposed response
   - See confidence score
4. **Decide**
   - Approve as-is → Move to `Approved/`
   - Edit → Modify response → Move to `Approved/`
   - Reject → Delete file
5. **Execute** → Orchestrator sends when file reaches `Approved/`
6. **Confirm** → File moves to `Done/`, logged to audit trail

### For Operations

Monitor email processing:

```bash
# View pending approvals
ls -la vault/Pending_Approval/

# Check recent actions
tail -f vault/Logs/$(date +%Y-%m-%d).json | jq '.[] | select(.action=="email_*")'

# View confidence distribution
grep "confidence" vault/Pending_Approval/*.md | awk -F: '{print $3}' | sort -n
```

---

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Email detection | ~20s | Poll interval |
| Drafter parsing | <100ms | Local file read |
| OpenAI API call | 2-5s | gpt-4o-mini generation |
| Draft file creation | <50ms | Local write |
| Total end-to-end | ~2.5-6s | Excluding human review |

**Throughput**: Up to 5 emails per 20-second polling cycle

---

## Error Handling

**Missing Email**:
- Logs warning
- Skips processing
- Does not crash

**OpenAI API Failure**:
- Logs error with API response
- Creates fallback draft
- Lower confidence score (0.5)
- Requires human review

**Malformed Inbox File**:
- Logs parsing error
- Moves to rejected folder
- Does not crash

**Duplicate Email**:
- Tracked via processed_ids
- Prevents duplicate drafts
- Idempotent

---

## Testing

Run `python3 test_keyword_escalation.py` to verify system:

- Email parsing: Extract metadata correctly
- Draft generation: Call OpenAI successfully
- File creation: Write to vault correctly
- Deduplication: No duplicate drafts

---

## Security

**HITL Safeguards**:
- All responses require human approval before sending
- AI confidence score visible to reviewer
- Easy rejection path (delete file)
- Audit logging of all approvals

**Data Handling**:
- Email content never logged to external systems
- OpenAI API calls made over HTTPS
- Credentials stored in .env (not committed to git)
- Local file operations only

**Compliance**:
- Audit trail records who approved each email
- Timestamps enable timeline reconstruction
- 90-day log retention

---

## Troubleshooting

**No drafts appearing**:
- Check OpenAI API key in .env
- Verify vault directory permissions
- Check orchestrator logs: `grep email vault/Logs/`

**Low confidence scores**:
- Review email content (ambiguous requests)
- Update Company_Handbook rules
- Consider fallback template

**Drafts not being executed**:
- Verify file is in vault/Approved/
- Check email MCP server status
- Review orchestrator logs for errors
