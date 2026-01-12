# Email Drafting Agent Skill

**Skill ID**: `email-drafting`
**Type**: Autonomous Reasoning / Email Generation
**Tier**: Silver/Gold
**Dependencies**: Claude API, Company_Handbook.md

## Purpose

Enable the AI Employee to autonomously read incoming emails, consult automation rules, and draft intelligent responses using Claude's reasoning engine. This transforms mechanical file processing into genuine intelligence.

## Architecture

```
Email Received (Needs_Action/)
    ↓
Email Drafter reads:
  ├─ Email content (from, subject, body)
  ├─ Company_Handbook.md (automation rules)
  └─ Contact metadata (known/unknown)
    ↓
Claude generates response:
  ├─ Understands email intent
  ├─ Applies business rules
  ├─ Drafts professional reply
  └─ Includes AI disclosure
    ↓
Creates Pending_Approval/
  ├─ Original email
  ├─ Claude's reasoning
  ├─ Draft response
  ├─ Auto-approve flag
  └─ Edit suggestions
    ↓
Human reviews (optional edit)
    ↓
Approval triggers Email MCP
    ↓
Response sent + logged
```

## Capabilities

### Email Understanding
- Extract sender, subject, intent from incoming emails
- Identify email category (inquiry, complaint, invoice, etc.)
- Classify urgency/priority

### Rule-Based Reasoning
- Consult Company_Handbook.md automation rules
- Check auto-approval thresholds:
  - Known contacts (auto-approve)
  - New contacts (require approval)
  - High-value requests (always approval)
- Apply business rules to response tone/content

### Claude-Powered Drafting
- Generate contextually appropriate responses
- Match business voice/tone
- Include relevant information
- Professional formatting

### Transparency & Safety
- Add AI disclosure signature
- Include reasoning explanation
- Flag confidence levels
- Suggest human review if uncertain

## Configuration (Company_Handbook.md)

```yaml
email_automation:
  # Auto-approve replies to known contacts
  known_contacts:
    - boss@company.com
    - clients@ourcompany.com
    - team@ourteam.com

  # Always require approval for:
  always_approve_required:
    - payments over $5000
    - contract terms
    - new client onboarding

  # Email response rules:
  response_rules:
    inquiry: "Respond within 24h, professional tone"
    complaint: "Empathetic, solution-focused, require approval"
    invoice: "Factual, reference invoice number, auto-approve if <$1000"
    job_inquiry: "Encouraging, provide timeline, require approval"

  # Signature
  ai_signature: |
    ---
    This reply was drafted by Claude AI Employee.
    [Human name] reviewed and approved this response.
```

## Usage Flow

1. **Email arrives** → `vault/Needs_Action/EMAIL_*.md`
2. **Orchestrator detects** → Triggers email drafter
3. **Claude drafts** → Analyzes email + rules → Generates response
4. **Creates approval file** → `vault/Pending_Approval/EMAIL_DRAFT_*.md`
   - Shows original
   - Shows Claude's reasoning
   - Shows draft response
   - Marks auto-approve status
5. **Human reviews** (takes 10 seconds for auto-approve, 2 min for approval-required)
6. **Approval moves file** → `vault/Approved/EMAIL_*.md`
7. **Orchestrator executes** → Sends via Gmail API
8. **Logged** → `vault/Done/` + `vault/Logs/`

## File Format (Auto-Generated)

```markdown
---
type: email_draft
original_from: boss@company.com
original_subject: Q1 Budget Review
created: 2026-01-09T10:30:00Z
auto_approve: true
confidence: 0.95
ai_generated: true
---

## Original Email

From: boss@company.com
Subject: Q1 Budget Review

Please review attached Q1 budget proposal...

---

## Claude's Analysis

**Email Type**: Inquiry/Request
**Intent**: Review and approve budget
**Priority**: High
**Suggested Tone**: Professional, confirmatory
**Confidence**: 95% (clear request)

**Applied Rules**:
- Known contact (boss@company.com) → Auto-approve enabled
- No financial amounts → No approval override
- Standard inquiry → Standard response template

---

## Proposed Response

Hi,

Thank you for sharing the Q1 budget proposal. I've reviewed the document and have the following observations:

[Claude generates specific, relevant response based on content]

I'll have detailed feedback by EOD tomorrow.

Best regards,
[Your name]

---

## Actions

- [x] Auto-approved (known contact)
- [ ] Edit response above
- [ ] Move to /Approved/ to send
- [ ] Reject and provide feedback

---

*AI-generated draft. Review before approval.*
```

## Integration Points

- **Orchestrator**: Triggers drafter on inbox events
- **Company_Handbook.md**: Source of automation rules
- **Claude API**: Generates intelligent responses
- **Gmail API**: Sends final approved responses
- **Audit Logger**: Records all drafts + approvals

## Safety Features

1. **AI Disclosure** - Every draft includes signature
2. **Confidence Scoring** - Claude rates how certain it is
3. **Reasoning Transparency** - Shows why it drafted that way
4. **Human Override** - Always reviewable/editable
5. **Approval Workflow** - Even auto-approves can be overridden

## Advanced Features

- **Contact Personalization**: Different tone for different contacts
- **Template Suggestions**: Learn from your past responses
- **Multi-language Support**: Draft in client's language
- **Escalation Rules**: Flag for human if uncertainty > threshold
- **Response Variants**: Offer alternative approaches for review

## Metrics Tracked

- Draft generation time (typically <2 seconds)
- Human approval time per email
- Claude confidence scores
- Auto-approve vs. manual approval ratio
- Response quality feedback loop
