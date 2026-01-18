# System Architecture - DigitalFTE

## Core Design Principles

1. **Local-first**: All data stoclean red locally in Obsidian vault
2. **HITL (Human-in-the-Loop)**: Sensitive actions require human approval
3. **Modular**: Each component (watcher, MCP, skill) is independent
4. **Resilient**: Graceful degradation when components fail
5. **Auditable**: Every action logged with full context

## Component Breakdown

### Perception Layer (Watchers)

Python scripts that monitor external inputs:

- **Gmail Watcher**: Polls Gmail API every 2 min for important emails
- **WhatsApp Watcher**: Processes Twilio webhook queue for keywords (urgent, invoice, payment, help)
- **LinkedIn Watcher**: Polls LinkedIn API for profile activity
- **FileSystem Watcher**: Monitors drop folder for new files

Each watcher:
- Creates markdown file in `/vault/Needs_Action/` on detection
- Logs event to `/vault/Logs/YYYY-MM-DD.json`
- Implements exponential backoff on API errors
- Maintains set of processed IDs (prevents duplicates)

### Memory Layer (Obsidian Vault)

Local markdown-based knowledge base:

```
/vault/
├── Dashboard.md              # Real-time system status
├── Company_Handbook.md       # Automation rules
├── Business_Goals.md         # KPIs & targets
├── Inbox/                    # ← Legacy watcher input (optional)
├── Needs_Action/             # ← Primary input for actions
├── Plans/                    # ← Claude reasoning
├── Pending_Approval/         # ← Awaiting human approval
├── Approved/                 # ← Ready to execute
├── Rejected/                 # ← Declined by human
├── Done/                     # ← Completed & archived
├── Accounting/               # Financial data
├── Briefings/                # CEO briefings
├── Social_Media/             # Content & analytics
└── Logs/                     # Audit trail
    ├── YYYY-MM-DD.json       # Daily logs
    ├── audit_rules.md        # Logging policy
    └── error_recovery.md     # Error handling strategy
```

File flow:
1. Watcher creates file in `/Needs_Action/`
2. Orchestrator detects change
3. Claude processes → Creates `/Plans/` reasoning file
4. Claude determines if action needed
5. If sensitive → Creates `/Pending_Approval/` for human
6. Human moves to `/Approved/` or `/Rejected/`
7. Orchestrator executes → Logs to `/Logs/`
8. File moves to `/Done/` → Archived

### Reasoning Layer (Claude Code)

AI decision-making engine:

- Reads `/Needs_Action/` for new items (also watches `/Inbox/` for legacy)
- Consults `Company_Handbook.md` for rules
- Creates `/Plans/` file with reasoning & next steps
- Determines if action is auto-approvable or requires HITL
- Uses Agent Skills to execute operations

### Action Layer (MCP Servers)

Model Context Protocol servers handle external actions:

- **Email MCP**: Send/draft/search emails (Gmail)
- **Browser MCP**: Placeholder for future browser automation (not used in Twilio flow)
- **Xero MCP**: Create invoices, log transactions (Xero API)
- **Meta Social MCP**: Post to Facebook/Instagram
- **Twitter MCP**: Post tweets, fetch metrics

Each MCP:
- Runs as Node.js subprocess
- Communicates via stdio with Claude Code
- Handles authentication & retries
- Logs actions to audit trail

### Orchestration Layer (Orchestrator.py)

Master process that coordinates everything:

- Starts all watcher processes (PM2 management)
- Watches vault folders for changes
- Triggers Claude Code on new `/Needs_Action/` files
- Executes MCP server actions on approval
- Maintains process health & auto-restarts failures
- Routes alerts to human

### Monitoring Layer (agents/watchdog.py)

System health monitor:

- Checks if critical processes are running every 60 sec
- Auto-restarts crashed watchers/orchestrator
- Logs process failures to audit trail
- Alerts human if system health degrades

## Data Flow Examples

### Email Processing Flow

```
Gmail API
  ↓ (Gmail Watcher)
Creates /Needs_Action/EMAIL_[ID].md
  ↓ (Orchestrator detects)
Triggers Claude Code
  ↓
Claude reads /Needs_Action/ file
Claude consults Company_Handbook.md
Claude creates /Plans/PLAN_[ID].md
  ├─ Auto-approvable? → Call Email MCP directly
  └─ Needs approval? → Create /Pending_Approval/[ID].md
      ↓
      Human reviews + moves to /Approved/
      ↓
      Orchestrator detects /Approved/ file
      ↓
      Calls Email MCP → Sends email
      ↓
      Logs to /Logs/[DATE].json
      ↓
      Moves to /Done/
```

### Payment Processing Flow

```
Bank notification / Manual input
  ↓
Claude detects payment needed
  ↓
Company_Handbook.md says:
- < $50 recurring known payee? Auto-approve
- New payee or > $100? HITL required
  ↓
If HITL:
  Create /Pending_Approval/PAYMENT_[ID].md
  ↓
  Human reviews and moves to /Approved/
  ↓
  Xero MCP executes payment
  ↓
  Logs to Xero + audit trail
```

### CEO Briefing Flow

```
Monday 9 AM (Periodic check in Orchestrator)
  ↓
orchestrator.py (generate_ceo_briefing)
  ↓
Reads:
- /vault/Business_Goals.md (targets)
- /vault/Done/ (completed tasks)
- /vault/Logs/ (daily transactions)
- Xero API (account balance)
- Social Media APIs (engagement)
  ↓
Calculates:
- Weekly revenue vs target
- Task completion rate
- Bottlenecks (tasks taking longer than expected)
- Unused subscriptions
  ↓
Generates markdown briefing:
- /vault/Briefings/2026-01-06_briefing.md
  ↓
Moves to /Done/ when processed
```

## Error Handling Strategy

### Transient Errors (Network, Rate Limits)
- Retry with exponential backoff (1s, 2s, 4s, max 60s)
- Log each attempt to audit trail
- Max 3 attempts before giving up

### Authentication Errors (Token Expired)
- Pause operations immediately
- Alert human via email
- Wait for human intervention
- Never auto-retry

### Logic Errors (Claude Misinterprets)
- Move suspicious file to `/vault/Needs_Review/`
- Alert human for manual verification
- Don't execute until human approves

### System Errors (Process Crashes)
- Watchdog detects crashed process
- Auto-restart with delay
- Log crash to audit trail
- Alert human if repeated failures

## Security Model

### Credential Management
- All secrets in `.env` (gitignored)
- Never logged to audit trail
- Environment variables loaded at startup
- Credentials rotated monthly

### Approval Thresholds
| Action | Threshold | Requires HITL |
|--------|-----------|---------------|
| Email reply (known) | Any | No |
| Email (new contact) | Any | Yes |
| Payment | < $50 recurring | No |
| Payment | >= $50 or new | Yes |
| Social post | Scheduled | No |
| Social post | Real-time reply | Yes |

### Audit Logging
- Every action logged with timestamp, actor, target
- Approval decisions tracked
- No sensitive data in logs (only action types)
- 90-day retention minimum
- Queryable JSON format

## Scalability

This architecture scales across:

1. **Multiple watchers** - Add new watchers without changing core system
2. **Multiple MCP servers** - Add new integrations (Slack, Calendar, etc)
3. **Multiple users** - Extend vault structure with user-specific folders
4. **New Agent Skills** - Register skills without modifying orchestrator

Future: Cloud FTE extensions for team-based automation.

---

**Status**: Phase 2 Complete (Scaffolding)
**Next**: Phase 3 (Dashboard) → Phase 4 (Validation)
