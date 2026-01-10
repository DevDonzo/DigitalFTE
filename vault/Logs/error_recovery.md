# Error Recovery Strategy

**Last Updated**: 2026-01-08

## Error Categories

### Transient (Retry with backoff)
- Network timeout → retry 3x
- Rate limit (429) → wait 60s
- Service unavailable (503) → exponential backoff

### Authentication (Stop & Alert)
- 401 Unauthorized → pause, alert human
- 403 Forbidden → check permissions
- Expired token → request new credentials

### Logic (Human Review)
- Claude misinterprets → /vault/Needs_Review/
- Invalid data → quarantine + alert
- Missing field → human review

### System (Auto-restart)
- Orchestrator crash → watchdog restarts
- Disk full → alert human
- Memory issue → watchdog monitors

---

## Component Failures

| Component | Failure Mode | Recovery |
|-----------|--------------|----------|
| Gmail | API down | Queue locally, retry later |
| Xero | Connection lost | HITL approval, no auto-retry |
| Claude | Unavailable | Queue in /Inbox/, process later |
| Vault | Locked | Write to /tmp/, sync when available |

---

## Monitoring

- Health check: Every 60 seconds
- Alert if: Process down > 5 min, API down > 10 min, disk < 1GB
- Alerts to: Email + /vault/Logs/
