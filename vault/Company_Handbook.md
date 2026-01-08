# Company Handbook - Rules of Engagement

**Last Updated**: 2026-01-08
**Version**: 1.0

This document defines the automation rules and escalation thresholds for your AI Employee.

---

## Automation Rules

### Email Handling
- Auto-reply to urgent emails from known contacts
- Flag new contacts for human review
- Archive after 48 hours
- Use approved templates from Social_Media/content_library.md

### Payments & Financial Actions
- Auto-approve: Recurring bills < $50
- HITL required: New payees, > $100, amount changes > 10%
- Always log to Xero
- Approval timeout: 24 hours

**Payment Thresholds**:
- < $50: Auto-approve if recurring
- $50-$500: HITL approval
- > $500: HITL + Xero verification

### Social Media Posting
- Auto-post: Scheduled content only
- HITL required: Real-time replies, @mentions
- Tone: Professional but friendly
- No promotional spam

### Xero Accounting
- Auto-create invoices from templates
- Log all transactions with audit trail
- HITL for all payments
- Auto-generate weekly CEO Briefing

---

## Escalation Thresholds

| Scenario | Threshold | Action |
|----------|-----------|--------|
| Revenue decision | > $5,000 | Email human |
| Critical error | System failure | Pause + alert |
| New vendor | Any | Request approval |
| Rate limit | API errors | Backoff + log |

---

## Error Handling

- System error → watchdog auto-restart
- API error → Exponential backoff
- Auth error → Pause + alert
- Data corruption → Quarantine + alert

---

## HITL Workflow

1. Claude creates approval file in `/Pending_Approval/`
2. Human moves to `/Approved/` or `/Rejected/`
3. Action executes on approval or archives on rejection
