# Audit Rules & Retention Policy

**Last Updated**: 2026-01-08
**Compliance**: 90-day minimum retention

---

## Required Log Fields

Every action logged to `/vault/Logs/YYYY-MM-DD.json` must include:

```json
{
  "timestamp": "2026-01-08T10:30:00Z",      // ISO 8601 UTC
  "action_type": "email_send",               // Enum from list below
  "actor": "claude_code",                    // Always "claude_code" for AI
  "target": "client@example.com",            // Recipient or entity affected
  "parameters": {                             // What was done
    "subject": "Invoice #123",
    "body_length": 245
  },
  "approval_status": "approved",             // pending/approved/rejected/auto
  "approved_by": "human_user",               // Who approved (if HITL)
  "result": "success",                       // success/failure
  "error": null,                             // Error message if failed
  "execution_time_ms": 1234                  // Performance tracking
}
```

---

## Action Types

**Email**: email_send, email_draft, email_archive, email_forward
**Payments**: payment_create, payment_approve, payment_reject, payment_execute
**Social**: post_create, post_schedule, post_publish, post_delete
**Financial**: invoice_create, transaction_log, account_reconcile
**System**: watcher_started, process_crashed, error_recovered

---

## Retention Policy

| Log Type | Retention | Location |
|----------|-----------|----------|
| Daily logs | 90 days minimum | `/vault/Logs/YYYY-MM-DD.json` |
| Monthly summaries | 12 months | `/vault/Logs/YYYY-MM.json` |
| Sensitive actions | 1 year+ | `/vault/Logs/sensitive/` |
| Archived logs | Long-term | `/vault/Logs/archive/` |

---

## Query Examples

**All payments from a vendor**:
```bash
grep "vendor_name" /vault/Logs/*.json | jq
```

**Failed actions**:
```bash
grep '"result": "failure"' /vault/Logs/*.json
```

**HITL approvals**:
```bash
grep '"approval_status": "approved"' /vault/Logs/*.json
```

**Daily summary**:
```bash
jq -s 'length' /vault/Logs/2026-01-08.json
```

---

## Privacy Considerations

- Do NOT log: Passwords, API keys, tokens, full email bodies
- DO log: Action type, timestamp, decision, outcome
- Sensitive info: Hash PII if necessary
- Review logs monthly for compliance

---

## Archive Strategy

Every 90 days:
1. Move old logs to `/vault/Logs/archive/YYYY-Q#/`
2. Compress with gzip
3. Verify integrity
4. Update retention tracking

Current archive status: *Pending first 90-day cycle*
