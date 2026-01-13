# Invoice Flow - Email to Xero Integration

This document explains how the Digital FTE processes invoices from email requests through to creation in Xero.

## Complete Flow: Email → Plan → Approval → Xero

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EMAIL RECEIVED: "Can you send me an invoice for January?"                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: EMAIL WATCHER DETECTS                                                │
│ watchers/gmail_watcher.py monitors Gmail API (every 20 seconds)               │
│ - Looks for emails with subject/body containing "invoice"                    │
│ - Creates file: /vault/Needs_Action/EMAIL_[ID].md                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
            /vault/Needs_Action/EMAIL_abc123.md
            ───────────────────────────────────
            ---
            type: email
            from: client@example.com
            subject: Invoice for January
            received: 2026-01-13T10:30:00Z
            priority: high
            status: pending
            ---
            
            Client A is asking for January invoice...
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: ORCHESTRATOR READS & REASONS                                          │
│ scripts/orchestrator.py runs continuously (every 10 seconds)                  │
│ - Reads /Needs_Action/EMAIL_abc123.md                                         │
│ - Calls OpenAI to understand request: "User wants invoice for January"        │
│ - Checks Company_Handbook.md for approval rules                               │
│ - Extracts client name and looks up amount from /Accounting/Rates.md          │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CREATE INVOICE DRAFT                                                  │
│ orchestrator.py → _maybe_create_invoice_draft()                              │
│ - Checks if amount can be auto-determined (from rates.md)                    │
│ - Creates draft file: /vault/Pending_Approval/INVOICE_DRAFT_[ts].md          │
│ - Status: "pending_approval" (requires human review before Xero creation)     │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
        /vault/Pending_Approval/INVOICE_DRAFT_2026_01_13.md
        ────────────────────────────────────────────────────
        ---
        type: invoice_draft
        contact_name: Client A
        contact_id: client_a_001
        amount: 1500.00
        description: January 2026 Services
        due_date: 2026-02-13
        status: pending_approval
        ---
        
        ## Invoice Draft
        
        **Client**: Client A (client@example.com)
        **Amount**: $1,500.00
        **Due Date**: 2026-02-13
        **Description**: January 2026 Services
        
        ### Suggested Actions
        - [ ] Review and edit details if needed
        - [ ] Move to /Approved/ to create invoice in Xero
        - [ ] Move to /Rejected/ to discard
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: HUMAN APPROVAL (HITL - Human in the Loop)                            │
│ You review the draft in Obsidian vault                                        │
│ - Opens /vault/Pending_Approval/ folder                                      │
│ - Reviews invoice details                                                    │
│ - Moves file to /Approved/ if correct                                        │
│   OR                                                                          │
│ - Moves file to /Rejected/ if incorrect                                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
        [User moves INVOICE_DRAFT_... to /Approved/]
                                     ↓
/vault/Approved/INVOICE_DRAFT_2026_01_13.md
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: EXECUTE - CREATE IN XERO                                              │
│ orchestrator.py → _execute_invoice()                                         │
│ - Detects file moved to /Approved/                                           │
│ - Extracts: contact_name, amount, description, due_date from YAML frontmatter│
│ - Calls Xero MCP server                                                      │
│ - Xero creates invoice with Invoice Details                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                    [Xero API Call via MCP]
                    
        POST /invoices
        {
            "contact_id": "client_a_001",
            "line_items": [{
                "description": "January 2026 Services",
                "quantity": 1,
                "unit_amount": 1500.00
            }],
            "due_date": "2026-02-13",
            "invoice_type": "ACCREC"
        }
                                     ↓
        ✅ Xero Invoice Created: INV-2026-001
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: SEND TO CLIENT (Optional)                                            │
│ orchestrator.py → _send_invoice_email()                                      │
│ - Email MCP server composes professional invoice email                       │
│ - Attaches PDF from Xero (if configured)                                     │
│ - Sends to client@example.com                                                │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
        ✅ Email sent to client@example.com
        Subject: "Invoice INV-2026-001 - $1,500.00"
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: LOGGING & CLEANUP                                                     │
│ orchestrator.py → _log_action()                                              │
│ - Logs to: /vault/Logs/2026-01-13.json                                       │
│ - Moves source email to: /Done/EMAIL_abc123.md                               │
│ - Moves invoice draft to: /Done/INVOICE_DRAFT_...md                          │
│ - Records: timestamp, action, status, approval_status, approved_by           │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
            /vault/Logs/2026-01-13.json
            ────────────────────────────
            {
                "timestamp": "2026-01-13T10:45:23.234Z",
                "action_type": "invoice_created",
                "actor": "orchestrator",
                "source_file": "EMAIL_abc123.md",
                "approval_status": "approved",
                "approved_by": "human",
                "xero_invoice_id": "INV-2026-001",
                "amount": 1500.00,
                "contact": "Client A",
                "status": "success"
            }
            
            /vault/Done/EMAIL_abc123.md ✅ COMPLETED
            /vault/Done/INVOICE_DRAFT_2026_01_13.md ✅ COMPLETED
```

---

## Data Sources Used in Each Step

### Step 2 - Rate Lookup (from /Accounting/Rates.md)
```markdown
# /vault/Accounting/Rates.md

## Hourly Rate
- Consulting: $150/hour
- Development: $200/hour

## Retainer Clients
- Client A: $1,500/month
- Client B: $2,000/month
```

Orchestrator looks up "Client A" → finds $1,500/month rate

### Step 3 - Approval Rules (from Company_Handbook.md)
```markdown
# /vault/Company_Handbook.md

## Invoice Thresholds
- Auto-approve invoices: < $500
- Human review required: ≥ $500

Since Client A invoice is $1,500 → Requires human approval
```

### Step 5 - Xero Credentials (from .env)
```bash
# .env (NOT committed to git)
XERO_CLIENT_ID=your_client_id
XERO_CLIENT_SECRET=your_client_secret
XERO_TENANT_ID=your_tenant_id
XERO_ACCESS_TOKEN=your_access_token
```

---

## Code References

### 1. Gmail Watcher Detection
**File**: `watchers/gmail_watcher.py`
```python
def _is_invoice_request(content):
    return 'invoice' in content.lower()
```

### 2. Invoice Draft Creation
**File**: `scripts/orchestrator.py:_maybe_create_invoice_draft()`
- Detects invoice keyword
- Looks up amount from rates.md
- Creates draft file
- Marks as pending_approval

### 3. Invoice Execution
**File**: `scripts/orchestrator.py:_execute_invoice()`
```python
def _execute_invoice(self, filepath, content):
    # Extract amount, contact, due_date from YAML
    contact_name = metadata.get('contact_name')
    amount = float(metadata.get('amount'))
    
    # Call Xero MCP
    self._call_xero_mcp_create_invoice(
        contact_name, amount, description, due_date
    )
```

### 4. Xero MCP Call
**File**: `scripts/orchestrator.py:_call_xero_mcp_create_invoice()`
- Makes HTTP POST to Xero API via MCP server
- Creates invoice in Xero
- Returns invoice ID
- Logs success

### 5. Logging
**File**: `scripts/orchestrator.py:_log_action()`
```python
log_entry = {
    'timestamp': datetime.now().isoformat(),
    'action_type': 'invoice_created',
    'actor': 'orchestrator',
    'approval_status': 'approved',
    'approved_by': 'human',
    'xero_invoice_id': xero_result.get('id'),
    'status': 'success'
}
```

---

## Auto-Approval vs Manual Approval

### Auto-Approve (< $500)
```python
if amount < 500:  # From Company_Handbook.md
    # Skip /Pending_Approval, create directly in Xero
    self._call_xero_mcp_create_invoice(...)
```

### Manual Approval (≥ $500)
```python
if amount >= 500:
    # Create draft in /Pending_Approval
    # Wait for human to move to /Approved
    # Then create in Xero
```

---

## Failure Scenarios

### Scenario 1: Missing Amount
**Error**: "Missing amount in invoice draft"
**Action**: Draft moved to /Needs_Review/
**Fix**: User edits draft, moves to /Approved again

### Scenario 2: Invalid Client Name
**Error**: "Could not find client in Xero"
**Action**: Logged in /vault/Logs/, email NOT sent
**Fix**: Update Company_Handbook.md with correct client mapping

### Scenario 3: Xero API Down
**Error**: "Connection timeout to Xero"
**Action**: Draft stays in /Approved/, retry next cycle
**Fix**: Watchdog retries automatically with exponential backoff

---

## FAQ

**Q: How does the system know how much to invoice?**
A: It looks up the amount from `/vault/Accounting/Rates.md`. If the amount isn't clear, the orchestrator creates a draft and flags it for manual review in `/Pending_Approval/`.

**Q: What if I want to change the amount before sending?**
A: Edit the YAML metadata in `/vault/Pending_Approval/INVOICE_DRAFT_*.md` before moving to `/Approved/`.

**Q: Does it send the invoice automatically?**
A: Not by default. After Xero creation, you must manually move the file to `/Approved/` to trigger the email. This ensures HITL safety.

**Q: Can I see all invoices created?**
A: Yes! Check:
- `/vault/Done/` for completed invoices
- `/vault/Logs/2026-01-13.json` for audit trail
- Xero dashboard for all invoices

**Q: What if the client doesn't respond to the email?**
A: The watchdog monitors the email logs. If you see "sent" but no "read", the CEO briefing flags it as a bottleneck.

---

**Last Updated**: January 13, 2026
**Version**: 1.0
**Status**: Production Ready
