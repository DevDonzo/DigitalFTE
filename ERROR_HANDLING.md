# Error Handling Strategy

## Overview

The Digital FTE system implements comprehensive error handling across all layers:
- **Watcher Layer**: Graceful degradation on API failures
- **Orchestration Layer**: Retry logic with exponential backoff
- **HITL Layer**: Human decision on critical errors
- **Audit Layer**: Complete error logging for compliance

---

## Error Categories

### 1. Transient Errors (Retryable)
**Definition**: Temporary failures that may succeed on retry

**Examples**:
- Network timeouts (Gmail API temporarily unavailable)
- Rate limiting (Twitter API limit exceeded)
- Temporary OAuth token expiration
- Brief database unavailability

**Handling**:
```python
@with_retry(max_attempts=3, base_delay=1, max_delay=60)
def fetch_emails():
    # Automatically retries with exponential backoff
    # 1st retry: 1 second
    # 2nd retry: 2 seconds
    # 3rd retry: 4 seconds
    return gmail_api.get_unread()
```

**Behavior**:
- Initial delay: 1 second
- Max delay: 60 seconds
- Max attempts: 3 (configurable)
- Logged in audit trail

---

### 2. Authentication Errors (Requires Manual Fix)
**Definition**: Credentials expired or invalid

**Examples**:
- Gmail OAuth token expired
- Xero API key invalid
- WhatsApp session terminated
- Twitter API key revoked

**Handling**:
```python
try:
    response = api_call()
except AuthenticationError as e:
    # Mark action as BLOCKED_AUTH
    action.status = "BLOCKED_AUTH"
    action.move_to("vault/Rejected/")
    audit_log.error(f"Auth failed: {e}", action_id=action.id)
    notify_user("Action blocked: Reauthenticate {service}")
```

**User Action Required**:
1. Check `.env` credentials
2. Re-authenticate via service dashboard
3. Update credentials in `.env`
4. Restart component

**Vault State**: Item moved to `Rejected/` with error note

---

### 3. Validation Errors (User Error)
**Definition**: Invalid input or configuration

**Examples**:
- Empty email recipient
- Negative payment amount
- Invalid date format
- Missing required field

**Handling**:
```python
def validate_invoice(invoice_data):
    if not invoice_data['amount'] or invoice_data['amount'] < 0:
        raise ValidationError("Invoice amount must be positive")

    if not invoice_data['recipient']:
        raise ValidationError("Recipient email required")

    # If validation fails, action rejected with specific error
```

**User Action Required**:
1. Review `Rejected/` item for error message
2. Fix data in source system
3. Manual re-approval

**Vault State**: Item moved to `Rejected/` with error explanation

---

### 4. Business Rule Violations (Approval Required)
**Definition**: Valid but requires human decision

**Examples**:
- Payment exceeds approval threshold
- New vendor payment (security review)
- Sensitive customer request
- Cross-department escalation

**Handling**:
```python
if payment_amount > APPROVAL_THRESHOLD:
    action.status = "PENDING_APPROVAL"
    action.move_to("vault/Pending_Approval/")
    action.reason = f"Amount ${payment_amount} exceeds threshold ${APPROVAL_THRESHOLD}"
    audit_log.info("Approval required", action_id=action.id, reason=action.reason)
```

**User Action Required**:
1. Review item in `Pending_Approval/`
2. Approve: move to `Approved/`
3. Reject: move to `Rejected/` with reason
4. System executes upon approval

**Vault State**: Item waits in `Pending_Approval/` until human decision

---

### 5. System Errors (Escalation)
**Definition**: Unexpected system-level failures

**Examples**:
- Vault file system full
- Database corruption
- MCP server crash
- Out of memory
- Disk I/O errors

**Handling**:
```python
try:
    # Any operation that might fail
    process_action(action)
except SystemError as e:
    action.status = "SYSTEM_ERROR"
    action.error_type = "CRITICAL"
    audit_log.critical(
        f"System error: {e}",
        action_id=action.id,
        stacktrace=traceback.format_exc()
    )
    # Stop processing, require manual intervention
    raise
```

**User Action Required**:
1. Check system resources: `df -h`, `free -h`
2. Review error in logs
3. Restart component or system
4. Contact support if persists

**Vault State**: Orphaned in `Plans/` or `Approved/` - requires manual cleanup

---

## Retry Strategy

### Exponential Backoff Implementation
```python
def retry_with_backoff(func, max_attempts=3):
    """Retry with exponential backoff"""
    base_delay = 1  # seconds
    max_delay = 60

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except TransientError as e:
            if attempt == max_attempts:
                raise  # Give up after final attempt

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            audit_log.warn(f"Retry attempt {attempt}, waiting {delay}s", error=str(e))
            time.sleep(delay)
```

### Retry Limits by Error Type

| Error Type | Max Attempts | Base Delay | Max Delay |
|------------|-------------|-----------|----------|
| Network timeout | 5 | 1s | 60s |
| API rate limit | 3 | 2s | 120s |
| OAuth token | 1 | N/A | N/A |
| Validation | 0 | N/A | N/A |
| Business rule | 0 | N/A | N/A |

---

## Error Logging

### Audit Log Format (JSONL)
```json
{
  "timestamp": "2026-01-08T10:30:45.123Z",
  "action_type": "email_send",
  "actor": "orchestrator",
  "action_id": "ACT_20260108_001",
  "result": "error",
  "error_type": "TransientError",
  "error_message": "SMTP connection timeout",
  "details": {
    "recipient": "boss@company.com",
    "retry_count": 2,
    "next_retry_at": "2026-01-08T10:30:60Z"
  }
}
```

### Logging Levels
- **INFO**: Normal operation, successful actions
- **WARN**: Recoverable errors, retries
- **ERROR**: Failed actions, human intervention needed
- **CRITICAL**: System failures, process halt required

---

## Error Flow Diagram

```
┌─────────────────────────────────────────────┐
│         Action Execution                     │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│     Error Occurs                             │
└────────────┬────────────────────────────────┘
             │
    ┌────────┴─────────┬──────────────┐
    │                  │              │
    ▼                  ▼              ▼
┌────────────┐  ┌──────────────┐  ┌──────────┐
│ Transient? │  │ Auth Error?  │  │ Validation
│ YES → RETRY│  │ YES → BLOCK  │  │ Error?
│ NO → NEXT  │  │ NO → NEXT    │  │ YES → REJECT
└────┬───────┘  └───┬──────────┘  │ NO → NEXT
     │             │              └────┬─────
     ▼             ▼                   │
  [RETRY WAIT]  [USER MUST REAUTH]    ▼
     │             │            ┌────────────┐
     └─────────────┴────────────→│ Business   │
                   │             │ Rule Check │
                   │             └─────┬──────┘
                   │                   │
                   │      ┌────────────┴───┐
                   │      │                │
                   │      ▼                ▼
                   │  [APPROVE]      [REJECT]
                   │      │                │
                   │      ▼                ▼
                   │  [EXECUTE]      [REJECTED]
                   │      │                │
                   └──────┴────────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │ SUCCESS or  │
                    │ FAILURE     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌────────────────┐
                    │ LOG TO AUDIT   │
                    │ MOVE TO DONE/  │
                    │ REJECTED       │
                    └────────────────┘
```

---

## Component-Specific Error Handling

### Gmail Watcher
```
┌─────────────────────────────────────┐
│ Check for new emails (every 120s)   │
└────────────┬────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ API Timeout? │
      └──┬────────┬──┘
         │        │
      YES│        │NO
         │        ▼
      RETRY   ┌──────────────┐
         │    │ Auth Failed? │
         │    └──┬────────┬──┘
         │       │        │
         │    YES│        │NO
         │       │        ▼
         │    BLOCK  ┌──────────────┐
         │       │   │ Parse OK?    │
         │       │   └──┬────────┬──┘
         │       │      │        │
         │       │   YES│        │NO
         │       │      │     SKIP
         │       │      ▼
         │       │  ┌──────────────┐
         │       │  │ Create inbox │
         │       │  │ file & log   │
         │       │  └──────────────┘
         │       │
         └───────┴──→ SLEEP 120s
                      RETRY
```

### Orchestrator
```
┌──────────────────────────────────────┐
│ Monitor vault/Inbox (file watcher)   │
└────────────┬───────────────────────┘
             │
             ▼
      ┌──────────────────┐
      │ New file? YES    │
      └──┬───────────┬──┘
         │           │
         ▼           ▼ NO → IDLE
    ┌─────────────┐
    │ Read file   │
    │ Call Claude │
    └──┬────┬─────┘
       │    │
      OK   FAIL
       │    │
       ▼    └──→ ┌──────────────────┐
    Create Plan  │ Log error        │
    in Plans/    │ Keep in Inbox    │
       │         │ (retry later)    │
       └────────→┌──────────────────┐
                 │ Move to Plans/   │
                 │ Request approval │
                 └──────────────────┘
```

### MCP Servers
```
┌─────────────────────────┐
│ Receive tool request    │
└────────────┬────────────┘
             │
             ▼
      ┌─────────────────┐
      │ Validate input  │
      └──┬──────────┬──┘
         │          │
       OK│ ERROR     │
         │          ▼
         │    ┌──────────────┐
         │    │ Return error │
         │    │ response     │
         │    └──────────────┘
         │
         ▼
    ┌──────────────┐
    │ Call API     │
    └──┬────┬──┬──┘
       │    │  │
      OK   AUTH TRANSIENT
       │   FAIL  ERROR
       │   │     │
       ▼   ▼     ▼
    SUCCESS BLOCK RETRY
       │   │     │
       └───┴─────┘
           │
           ▼
    ┌─────────────┐
    │ Return      │
    │ response    │
    │ (+ logs)    │
    └─────────────┘
```

---

## Common Error Messages

### 501 "Email send failed"
```
Result: failed
Details: SMTP connection timeout after 30s
Action: Automatic retry in 1-2 seconds
Status: Pending_Approval → Approved (will execute on retry)
```

### 502 "Xero invoice creation blocked"
```
Result: error
Details: Authentication failed - token expired
Action: Manual re-authentication required
Status: Approved → Rejected (requires user action)
Fix: Update XERO_API_KEY in .env, restart orchestrator
```

### 503 "WhatsApp watcher crashed"
```
Result: critical
Details: Browser process terminated unexpectedly
Action: Automatic restart via watchdog (after 10s)
Status: Logs/2026-01-08.json (error_type: SYSTEM_ERROR)
Fix: Check system resources, restart watcher manually
```

---

## Recovery Procedures

### Partial Execution (action halfway done)
```bash
# 1. Check what happened
tail vault/Logs/*.json | jq 'select(.action_id=="ACT_123")'

# 2. Verify end state
ls vault/{Approved,Done,Rejected}/ACT_123*

# 3. Resume or skip
# Move to Done if completed
# Move to Pending_Approval if needs review
```

### Corrupted Vault State
```bash
# 1. Backup current vault
cp -r vault vault.backup

# 2. Identify orphaned files
find vault -name "*.md" -mtime +7 | head

# 3. Manually fix orphans
# Move stale items to Rejected or Done

# 4. Validate structure
python Setup_Verify.py
```

### Complete System Reset
```bash
# 1. Stop all processes
killall python3

# 2. Clear cache and tokens
rm -f token.pickle credentials.json

# 3. Clear vault (keep backups)
rm -rf vault
mkdir -p vault/{Inbox,Plans,Needs_Action,Pending_Approval,Approved,Rejected,Done,Logs}

# 4. Restart system
python scripts/orchestrator.py &
python watchers/gmail_watcher.py &
```

---

## Best Practices

### 1. Always Log Errors
```python
# ✅ Good: Informative error log
audit_log.error(
    "Email send failed after 3 retries",
    action_id=action.id,
    recipient=email.to,
    error=str(exception),
    retry_count=3
)

# ❌ Bad: Silent failure
try:
    send_email()
except:
    pass  # No logging
```

### 2. Use Specific Exceptions
```python
# ✅ Good: Specific exception handling
try:
    api_call()
except ConnectionError:
    retry()  # Transient, retry
except AuthenticationError:
    escalate()  # Auth, manual fix
except ValueError:
    reject()  # Validation, reject

# ❌ Bad: Generic exception handling
try:
    api_call()
except Exception:
    retry()  # Might retry non-transient errors
```

### 3. Set Reasonable Timeouts
```python
# ✅ Good: Configurable timeout
api_call(timeout=TIMEOUT_SECONDS)

# ❌ Bad: No timeout, hangs forever
api_call()  # Might hang indefinitely
```

### 4. Include Context in Errors
```python
# ✅ Good: Helpful context
raise ValidationError(
    f"Email validation failed for {user_email}: "
    f"'{user_email}' does not match pattern {EMAIL_PATTERN}"
)

# ❌ Bad: Vague error
raise ValidationError("Email validation failed")
```

---

## Monitoring & Alerting

### Health Check Script
```bash
#!/bin/bash
# Check system health

echo "Watcher status:"
pgrep -l gmail_watcher && echo "✓ Gmail" || echo "✗ Gmail"
pgrep -l whatsapp_watcher && echo "✓ WhatsApp" || echo "✗ WhatsApp"

echo -e "\nRecent errors (last hour):"
jq 'select(.result=="error")' vault/Logs/*.json | jq '.action_type' | sort | uniq -c

echo -e "\nPending approvals:"
ls vault/Pending_Approval | wc -l

echo -e "\nDisk usage:"
du -sh vault/
```

### Create Alert on Errors
```bash
# Monitor errors in real-time
tail -f vault/Logs/*.json | jq 'select(.result=="error")'

# Alert on critical errors
tail -f vault/Logs/*.json | jq 'select(.error_type=="CRITICAL")' && \
  osascript -e 'display notification "Critical error in DigitalFTE"'
```

---

See `ARCHITECTURE.md` for system design or `TROUBLESHOOTING.md` for specific issues.
