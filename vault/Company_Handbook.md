# Company Handbook - Rules of Engagement

**Last Updated**: 2026-01-08
**Version**: 1.0

This document defines the automation rules and escalation thresholds for your AI Employee.

---

## Automation Rules

### Email Handling (Claude-Powered Drafting)

**Known Contacts (Auto-Approve Replies)**:
- boss@company.com
- team@company.com
- clients@company.com
- support@company.com

**Response Rules by Email Type**:
- **Inquiry**: Professional tone, factual, <2 hour response target
- **Complaint**: Empathetic, solution-focused, ALWAYS human approval required
- **Invoice/Payment**: Factual, reference numbers, auto-approve if < $1000
- **Meeting Request**: Confirmatory, check calendar, auto-approve
- **New Contact**: Warm but cautious, ALWAYS human approval required

**General Rules**:
- Generate responses using Claude AI reasoning
- Include AI disclosure: "This reply was drafted by AI, reviewed by [name]"
- Archive processed emails after human approval
- Log all responses to audit trail
- Flag low confidence drafts (< 80%) for review
- Always require approval for non-business topics

### Payments & Financial Actions
- Auto-approve: Recurring bills < $50
- HITL required: New payees, > $100, amount changes > 10%
- Always log to Odoo accounting system
- Approval timeout: 24 hours

**Payment Thresholds**:
- < $50: Auto-approve if recurring
- $50-$500: HITL approval
- > $500: HITL + Odoo verification

### Social Media Posting

**Supported Platforms**: Twitter/X, Facebook, Instagram, LinkedIn

**How to Queue Posts**:
1. Create file in `/vault/Social_Media/`
2. Name format: `TWEET_[name].md`, `FACEBOOK_[name].md`, or `LINKEDIN_[name].md`
3. Move to `/Approved/` when ready to post
4. Orchestrator auto-posts within 5 seconds
5. Result logged to `/vault/Logs/social_posts.jsonl`

**Auto-Post Rules**:
- ✅ Scheduled announcements (pre-written, no real-time approval needed)
- ✅ Content from content library (pre-approved formats)
- ⚠️ Real-time replies (@mentions, trending topics) - HITL required
- ⚠️ Controversial or political content - HITL required
- ❌ Promotional spam or duplicate content

**Tone Guidelines**:
- Twitter: Professional, concise, thought leadership
- Facebook: Friendly, conversational, broader audience
- LinkedIn: Professional, insights-focused, career-oriented
- Instagram: Visual-first, authentic, personal

**Engagement Tracking**:
- Likes, shares, comments logged automatically
- Weekly engagement summary in CEO Briefing
- Audience growth metrics tracked

### Odoo Accounting
- Auto-create invoices and bills from templates
- Log all transactions with audit trail
- HITL for all payments
- Auto-generate weekly CEO Briefing with P&L reports

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
