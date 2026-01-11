# GOLD TIER Digital FTE - Technical Specification

**Project**: Personal AI Employee Hackathon - GOLD Tier
**Target Status**: Autonomous Full-Time Equivalent Agent
**Architecture**: Claude Code + Obsidian + MCP Servers + Python Watchers
**Estimated Duration**: 40+ hours
**Demo Date**: Wednesday weekly Research Meetings

---

## Executive Summary

This specification maps every Bronze, Silver, and Gold tier requirement from the Panaversity Hackathon to specific technical components, files, and verification criteria. It serves as the **single source of truth** for all implementation decisions.

---

## Part I: Requirements Matrix & Traceability

### Bronze Tier Requirements (Foundation - 8-12 hours)

| # | Requirement | Technical Component | Implementation File(s) | Agent Skill | Verification | Status |
|---|---|---|---|---|---|---|
| B1 | Obsidian vault with Dashboard.md | Dashboard System | `vault/Dashboard.md` | N/A | File exists + contains project overview | |
| B2 | Company_Handbook.md | Rules of Engagement | `vault/Company_Handbook.md` | N/A | File exists + defines automation rules | |
| B3 | One working Watcher (Gmail OR FileSystem) | Perception Layer | `watchers/gmail_watcher.py` OR `watchers/filesystem_watcher.py` | email-monitor OR filesystem-monitor | Watcher script runs without errors | |
| B4 | Claude Code reads/writes vault | File System Integration | Claude Code filesystem tools | N/A | Can read/write files via Claude Code | |
| B5 | Basic folder structure (/Inbox, /Needs_Action, /Done) | Vault Architecture | `vault/{Inbox,Needs_Action,Done}/` | N/A | Folders exist with correct names | |
| B6 | AI functionality as Agent Skills | Skill Architecture | `skills/*.md` (minimum 3 skills) | At least 3 defined | Skill files present + properly formatted | |

### Silver Tier Requirements (Functional Assistant - 20-30 hours)

| # | Requirement | Technical Component | Implementation File(s) | Agent Skill | Verification | Status |
|---|---|---|---|---|---|---|
| S1 | Two+ Watchers: Gmail + WhatsApp + LinkedIn | Multi-Watcher System | `watchers/{gmail,whatsapp,linkedin}_watcher.py` | email-monitor, whatsapp-monitor, linkedin-automation | All 3 watchers functional + integrated | |
| S2 | Auto-post on LinkedIn for business/sales | Social Media Automation | `skills/linkedin-automation.md` + LinkedIn API | linkedin-automation | Can schedule and post to LinkedIn | |
| S3 | Claude reasoning loop creating Plan.md files | Planning System | `scripts/orchestrator.py` + Claude prompt logic | reasoning-loop | Plan.md files created with reasoning | |
| S4 | One working MCP server for external action | Email MCP Integration | `mcp_servers/email_mcp/` + `mcp_config.json` | email-integration | MCP server configured + can send emails | |
| S5 | HITL approval workflow for sensitive actions | Human-in-the-Loop System | `vault/{Pending_Approval,Approved,Rejected}/` + `scripts/orchestrator.py` | request-approval | Approval files movable, actions trigger on approval | |
| S6 | Basic scheduling via cron or Task Scheduler | Scheduling System | System cron job OR Windows Task Scheduler | orchestration | Scheduled tasks execute on time | |
| S7 | AI functionality as Agent Skills | Skill Architecture | `skills/*.md` (minimum 6 skills) | 6+ defined | All Silver features have corresponding skills | |

### Gold Tier Requirements (Autonomous Employee - 40+ hours)

| # | Requirement | Technical Component | Implementation File(s) | Agent Skill | Verification | Status |
|---|---|---|---|---|---|---|
| G1 | All Silver requirements complete | Cross-Domain Foundation | All Silver components + Gold additions | All previous skills | Silver tier fully operational | |
| G2 | Full cross-domain integration (Personal + Business) | Unified Orchestration | `scripts/orchestrator.py` (enhanced), `vault/Company_Handbook.md` | orchestration-master | System handles personal (Gmail, Bank) + business (Social, Xero) seamlessly | |
| G3 | Xero accounting system creation + MCP integration | Accounting MCP Server | `mcp_servers/xero_mcp/` + `vault/Accounting/xero_config.md` + OAuth setup | xero-integration | Xero account created + MCP authenticated + can read/write transactions | |
| G4 | Facebook + Instagram integration (post + summary) | Meta Social MCP Server | `mcp_servers/meta_social_mcp/` + `vault/Social_Media/content_library.md` | social-post, social-summary | Can post to FB/IG + generate engagement summaries | |
| G5 | Twitter/X integration (post + summary) | Twitter MCP Server | `mcp_servers/twitter_mcp/` + API authentication | social-post, social-summary | Can post to Twitter/X + generate thread summaries | |
| G6 | Multiple MCP servers operational | MCP Orchestration | `mcp_config.json` + 5+ MCP servers | N/A | All MCP servers (email, browser, xero, meta, twitter) configured + running | |
| G7 | Weekly Business Audit + CEO Briefing | CEO Briefing System | `scripts/weekly_audit.py` + `vault/Briefings/` + cron job | ceo-briefing | Sunday 11 PM: audit executes, briefing generated in `vault/Briefings/YYYY-MM-DD_briefing.md` | |
| G8 | Error recovery + graceful degradation | Error Handling System | `utils/retry_handler.py` + `scripts/watchdog.py` + error recovery logic | error-recovery | Failed operations retry with backoff, system logs errors + continues | |
| G9 | Comprehensive audit logging (90-day retention) | Audit Logging System | `utils/audit_logger.py` + `vault/Logs/YYYY-MM-DD.json` | audit-logging | Every action logged to JSON, logs retained 90+ days, queryable | |
| G10 | Architecture documentation + lessons learned | Documentation | `README.md`, `ARCHITECTURE.md`, `LESSONS_LEARNED.md`, demo video | N/A | Docs complete + explain all components + demo shows system in action | |
| G11 | All AI functionality as Agent Skills | Skill Architecture | `skills/*.md` (9+ skills) | 9+ defined | All AI operations (9 core skills) implemented as reusable skills | |

---

## Part II: Detailed Technical Component Mapping

### 1. Xero Accounting Integration (GOLD - G3)

**Purpose**: Autonomous business accounting and financial tracking

**Account Setup** (Pre-Implementation):
1. Sign up at https://www.xero.com/signup/
2. Create organization + bank connections
3. Go to Settings → General Settings → Connected Apps
4. Register OAuth 2.0 App (https://developer.xero.com/)
5. Save credentials:
   - Client ID
   - Client Secret
   - Redirect URI: `http://localhost:8080/callback`
6. Download `credentials.json`

**Technical Files**:
- `mcp_servers/xero_mcp/index.js` - Xero MCP server implementation
- `mcp_servers/xero_mcp/package.json` - Dependencies (xero-node SDK)
- `vault/Accounting/xero_config.md` - Configuration + organization details
- `vault/Accounting/Current_Month.md` - Monthly transaction log
- `vault/Accounting/Rates.md` - Billing rates for invoicing
- `utils/audit_logger.py` - Logs all financial transactions

**MCP Server Configuration** (in `mcp_config.json`):
```json
{
  "name": "xero",
  "command": "node",
  "args": ["/path/to/xero_mcp/index.js"],
  "env": {
    "XERO_CLIENT_ID": "${XERO_CLIENT_ID}",
    "XERO_CLIENT_SECRET": "${XERO_CLIENT_SECRET}",
    "XERO_REDIRECT_URI": "http://localhost:8080/callback"
  }
}
```

**Agent Skill**: `xero-integration`
- Input: Transaction data, invoice details, account info
- Output: Transaction confirmation, balance reports, error handling
- Safeguards: HITL for payments > $500, rate limiting

**Verification Criteria**:
- [ ] Xero MCP server runs without errors
- [ ] OAuth authentication successful
- [ ] Can fetch account balance
- [ ] Can create invoice in Xero
- [ ] Transactions logged to audit trail
- [ ] Setup_Verify.py detects: `mcp_servers/xero_mcp/`, `vault/Accounting/xero_config.md`, XERO_CLIENT_ID in .env

---

### 2. CEO Briefing System (GOLD - G7)

**Purpose**: Weekly autonomous business audit and executive summary

**Schedule**: Sunday 11:00 PM (cron on Unix, Task Scheduler on Windows)

**Technical Files**:
- `scripts/weekly_audit.py` - Main audit logic
- `vault/Business_Goals.md` - Baseline metrics + targets
- `vault/Briefings/YYYY-MM-DD_CEO_Briefing.md` - Generated output
- `vault/Logs/YYYY-MM-DD.json` - Source data for audit

**Audit Components**:
1. **Revenue Calculation**: Sum transactions in `vault/Accounting/Current_Month.md`
2. **Task Analysis**: Review `/Done` folder for completed items
3. **Bottleneck Detection**: Compare expected vs actual task duration
4. **Subscription Audit**: Identify unused subscriptions from transaction patterns
5. **Proactive Suggestions**: Compare current spend vs targets

**Cron Schedule** (Unix):
```bash
0 23 * * 0 python /path/to/scripts/weekly_audit.py
```

**Task Scheduler** (Windows):
- Trigger: Weekly, Sunday 11:00 PM
- Action: `python C:\path\to\scripts\weekly_audit.py`

**Agent Skill**: `ceo-briefing`
- Input: Business goals, transactions, task logs, social metrics
- Output: Markdown briefing with executive summary
- Safeguards: Only suggestions (no automatic actions)

**Briefing Template Output**:
```markdown
# Monday Morning CEO Briefing
**Period**: [Sunday to Sunday]
**Generated**: [Timestamp]

## Executive Summary
[One-liner assessment]

## Financial Summary
- **Weekly Revenue**: $X,XXX
- **Monthly Target**: $10,000
- **MTD Progress**: Y%
- **Trend**: [On track / Behind / Ahead]

## Key Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Invoice payment rate | >90% | X% | ✓/⚠ |
| Client response time | <24h | Xh | ✓/⚠ |

## Completed Tasks
- [ ] Task 1
- [ ] Task 2

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|

## Proactive Suggestions
### Cost Optimization
- Notion: No activity 45 days → Cancel $15/mo?
- [ACTION] Move to /Pending_Approval

### Upcoming Deadlines
- Jan 15: Project Alpha Final Delivery
- Jan 31: Q1 Tax Prep

---
*Generated by AI Employee v0.1*
```

**Verification Criteria**:
- [ ] `scripts/weekly_audit.py` exists + runs without errors
- [ ] `vault/Briefings/` directory exists
- [ ] Cron/Task Scheduler job configured correctly
- [ ] Briefing file generated every Sunday 11 PM
- [ ] Briefing contains all required sections
- [ ] Setup_Verify.py detects all components + scheduled job

---

### 3. Social Media Integration (GOLD - G4, G5)

**Facebook + Instagram (Meta)** & **Twitter/X**

#### Account Setup

**Meta Business** (Facebook + Instagram):
1. Create Meta Business Account: https://business.facebook.com/
2. Create Facebook Page + Instagram Professional Account
3. Meta Developer Account: https://developers.facebook.com/
4. Create App → Add Facebook Login + Instagram Basic Display
5. Generate User Access Token (expires) + Page Access Token (indefinite)
6. Save credentials

**Twitter/X**:
1. Apply for Developer Account: https://developer.twitter.com/
2. Create Project + App
3. Generate API Key, API Secret, Bearer Token
4. Enable OAuth 2.0 (if needed for future features)
5. Save credentials

#### Technical Files

**Meta Social MCP**:
- `mcp_servers/meta_social_mcp/index.js` - Facebook/Instagram MCP
- `mcp_servers/meta_social_mcp/package.json` - Dependencies

**Twitter MCP**:
- `mcp_servers/twitter_mcp/index.js` - Twitter MCP
- `mcp_servers/twitter_mcp/package.json` - Dependencies

**Shared Files**:
- `vault/Social_Media/posting_schedule.md` - Content calendar
- `vault/Social_Media/content_library.md` - Reusable content
- `vault/Social_Media/engagement_summary.md` - Weekly analytics

**MCP Configuration** (in `mcp_config.json`):
```json
{
  "name": "meta_social",
  "command": "node",
  "args": ["/path/to/meta_social_mcp/index.js"],
  "env": {
    "FACEBOOK_ACCESS_TOKEN": "${FACEBOOK_ACCESS_TOKEN}",
    "INSTAGRAM_BUSINESS_ACCOUNT_ID": "${INSTAGRAM_BUSINESS_ACCOUNT_ID}"
  }
},
{
  "name": "twitter",
  "command": "node",
  "args": ["/path/to/twitter_mcp/index.js"],
  "env": {
    "TWITTER_API_KEY": "${TWITTER_API_KEY}",
    "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
    "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}"
  }
}
```

**Agent Skills**:
- `social-post` (Facebook, Instagram, Twitter)
  - Input: Content, platform, schedule time
  - Output: Post ID, scheduled confirmation
  - Safeguards: Content review via HITL, rate limiting

- `social-summary` (Weekly engagement report)
  - Input: Account data from past week
  - Output: Engagement metrics, content performance
  - Safeguards: Data-only, no actions

**Verification Criteria**:
- [ ] Both MCP servers in `mcp_config.json`
- [ ] OAuth tokens in `.env` file
- [ ] Can post to Facebook successfully
- [ ] Can post to Instagram successfully
- [ ] Can post to Twitter/X successfully
- [ ] Engagement summaries generated
- [ ] Setup_Verify.py detects both MCP servers + credentials

---

### 4. Human-in-the-Loop (HITL) Approval Workflow (GOLD - G1, Silver - S5)

**Purpose**: Prevent AI mistakes on sensitive actions without sacrificing autonomy

**Folder Architecture**:
- `/vault/Pending_Approval/` - AI-generated approval requests
- `/vault/Approved/` - Human-approved actions ready for execution
- `/vault/Rejected/` - Human-rejected actions (logged for review)

**Workflow**:

1. **Detection** (Claude Code)
   - Claude encounters a sensitive action (payment, email to new contact, social post)
   - Creates file: `/vault/Pending_Approval/[ACTION_TYPE]_[DETAILS]_[TIMESTAMP].md`

2. **Human Review**
   - Human reviews file in Obsidian or file system
   - Reads details: action, recipient, amount, reasoning

3. **Decision**
   - Approve: Move to `/vault/Approved/`
   - Reject: Move to `/vault/Rejected/` (with notes)

4. **Execution**
   - Orchestrator watches `/vault/Approved/` folder
   - Detects new files, triggers corresponding MCP action
   - Moves file to `/vault/Done/` after successful execution

5. **Audit Logging**
   - All approvals logged to `/vault/Logs/YYYY-MM-DD.json`
   - Includes: action, human decision, timestamp, result

**Technical Files**:
- `scripts/orchestrator.py` - Watches approval folders + triggers actions
- `vault/Pending_Approval/` - Approval request storage
- `vault/Approved/` - Approved actions queue
- `vault/Rejected/` - Rejection history
- `utils/audit_logger.py` - Logs all approval decisions

**Approval Request Template** (Example: Payment):

```markdown
---
type: approval_request
action: payment
timestamp: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

# Payment Approval Request

**Recipient**: Client A (email: client@example.com)
**Amount**: $500.00
**Reference**: Invoice #1234
**Reason**: January services payment
**AI Reasoning**: Client requested invoice via WhatsApp, invoice generated, amount matches contract rate.

## Transaction Details
- Bank Account: Checking (ends in 1234)
- Expected Arrival: 1-2 business days
- Fee: $0.00

## Actions
- ✅ **APPROVE**: Move this file to `/Approved` folder
- ❌ **REJECT**: Move this file to `/Rejected` folder (add notes below)

## Rejection Notes
[Leave blank if approving]
```

**Agent Skill**: `request-approval`
- Input: Action type, recipient, amount, reasoning
- Output: Approval request file + wait for human decision
- Safeguards: Enforces file naming, captures all decision metadata

**Approval Thresholds** (from Security Architecture):

| Action Category | Auto-Approve | Always Require Approval |
|---|---|---|
| **Email** | To known contacts | New contacts, bulk sends |
| **Payment** | < $50 (recurring) | New payees, > $100 |
| **Social Media** | Scheduled posts | Live replies, DMs |
| **Deletion** | Never auto-approve | All file deletions |

**Verification Criteria**:
- [ ] All 3 approval folders exist
- [ ] Orchestrator script monitors `/Approved` folder
- [ ] Approval request files follow template
- [ ] File moves trigger corresponding action
- [ ] All decisions logged to audit trail
- [ ] Setup_Verify.py verifies folder structure + orchestrator logic

---

### 5. Watchers (Perception Layer - Bronze, Silver, Gold)

**Purpose**: Autonomous detection of events that trigger Claude Code processing

**Watcher Types**:

#### 5.1 Gmail Watcher (Bronze - B3)

**File**: `watchers/gmail_watcher.py`

**Account Setup**:
1. Google Cloud Console: https://console.cloud.google.com/
2. Create project → Enable Gmail API
3. Create OAuth 2.0 Credentials (Desktop app)
4. Download `credentials.json`
5. First run: Browser opens → Grant permission → Token saved locally

**Functionality**:
- Polls Gmail API every 2 minutes
- Filters: `is:unread is:important`
- Creates file: `/vault/Inbox/EMAIL_[SENDER]_[TIMESTAMP].md`
- Template includes: sender, subject, snippet, suggested actions

**Technical Details**:
- Uses `google-auth-oauthlib` for OAuth
- Maintains set of processed message IDs (prevents duplicates)
- Exponential backoff on API errors
- Logs to `vault/Logs/YYYY-MM-DD.json`

**Configuration** (in `.env`):
```
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_CHECK_INTERVAL=120
```

**Verification Criteria**:
- [ ] `watchers/gmail_watcher.py` exists
- [ ] Google Cloud project + Gmail API enabled
- [ ] `credentials.json` downloaded + stored
- [ ] Watcher runs without errors
- [ ] Creates email files in `/vault/Inbox/`
- [ ] Setup_Verify.py confirms file exists + executable

---

#### 5.2 WhatsApp Watcher (Silver - S1)

**File**: `watchers/whatsapp_watcher.py`

**Account Setup**:
- No API signup needed
- Uses WhatsApp Web automation via Playwright
- First run: Scan QR code to link browser session

**Functionality**:
- Uses Playwright to control headless Chrome browser
- Monitors WhatsApp Web for messages with keywords: "urgent", "asap", "invoice", "payment", "help"
- Creates file: `/vault/Inbox/WHATSAPP_[CONTACT]_[TIMESTAMP].md`
- Keeps browser session persistent (no re-login needed)

**Technical Details**:
- Playwright launches persistent browser context
- Looks for unread message indicators
- Extracts message text + sender info
- Creates actionable markdown for Claude

**Configuration** (in `.env`):
```
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session
WHATSAPP_CHECK_INTERVAL=30
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help
```

**Verification Criteria**:
- [ ] `watchers/whatsapp_watcher.py` exists
- [ ] Playwright + dependencies installed
- [ ] WhatsApp Web session linked (manual QR scan)
- [ ] Watcher detects incoming messages
- [ ] Creates message files in `/vault/Inbox/`
- [ ] Setup_Verify.py confirms file exists

---

#### 5.3 LinkedIn Watcher (Silver - S1)

**File**: `watchers/linkedin_watcher.py`

**Account Setup**:
1. LinkedIn Developer Application: https://www.linkedin.com/developers/
2. Create app → Get credentials
3. Generate access token (user access token for personal LinkedIn account)
4. Save credentials to `.env`

**Functionality**:
- Polls LinkedIn API for profile updates (posts, engagement, messages)
- Creates file: `/vault/Inbox/LINKEDIN_[EVENT]_[TIMESTAMP].md`
- Monitors for: new profile views, message requests, engagement metrics

**Configuration** (in `.env`):
```
LINKEDIN_ACCESS_TOKEN=your_token_here
LINKEDIN_CHECK_INTERVAL=300
```

**Verification Criteria**:
- [ ] `watchers/linkedin_watcher.py` exists
- [ ] LinkedIn developer app created + token generated
- [ ] Watcher runs without errors
- [ ] Creates event files in `/vault/Inbox/`
- [ ] Setup_Verify.py confirms file exists

---

#### 5.4 FileSystem Watcher (Bronze - B3)

**File**: `watchers/filesystem_watcher.py`

**Functionality**:
- Monitors a designated "drop folder" for new files
- Copies files to `/vault/Inbox/FILE_[NAME]_[TIMESTAMP]`
- Creates metadata file with file info (size, date, type)
- No external API required

**Technical Details**:
- Uses `watchdog` library to monitor directory
- On file creation: copies to vault + creates .md metadata
- Handles various file types (PDF, images, spreadsheets)

**Configuration** (in `.env`):
```
WATCH_FOLDER=/Users/hparacha/Downloads
WATCH_VAULT=/Users/hparacha/DigitalFTE/vault
```

**Verification Criteria**:
- [ ] `watchers/filesystem_watcher.py` exists
- [ ] watchdog library installed
- [ ] Drop folder specified in config
- [ ] Watcher detects new files
- [ ] Files copied + metadata created
- [ ] Setup_Verify.py confirms file exists

---

### 6. MCP Server Architecture (GOLD - G6)

**Purpose**: External action execution for Claude Code

**Required MCP Servers** (5 minimum for Gold):

1. **Email MCP** (Silver requirement)
   - Location: `mcp_servers/email_mcp/`
   - Capabilities: Send, draft, search emails
   - Source: Use pre-built `email-mcp` or build custom
   - Config: Gmail API credentials

2. **Browser MCP** (Silver requirement)
   - Location: `mcp_servers/browser_mcp/`
   - Capabilities: Navigate, click, fill forms, take screenshots
   - Source: Use Anthropic's browser-mcp or build custom
   - Config: Playwright/Selenium setup

3. **Xero MCP** (Gold requirement)
   - Location: `mcp_servers/xero_mcp/`
   - Capabilities: Fetch accounts, create invoices, log transactions
   - Config: Xero OAuth credentials

4. **Meta Social MCP** (Gold requirement)
   - Location: `mcp_servers/meta_social_mcp/`
   - Capabilities: Post to Facebook/Instagram, fetch engagement
   - Config: Meta access tokens

5. **Twitter MCP** (Gold requirement)
   - Location: `mcp_servers/twitter_mcp/`
   - Capabilities: Post tweets, fetch metrics, reply
   - Config: Twitter API credentials

**Optional MCP Servers**:
- Calendar MCP (create, update events)
- Slack MCP (send messages, read channels)
- Database MCP (read/write structured data)

**Configuration File** (`mcp_config.json`):
```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email_mcp/index.js"],
      "env": {
        "GMAIL_API_KEY": "${GMAIL_API_KEY}"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@anthropic/browser-mcp"],
      "env": {
        "HEADLESS": "true"
      }
    },
    {
      "name": "xero",
      "command": "node",
      "args": ["/path/to/xero_mcp/index.js"],
      "env": {
        "XERO_CLIENT_ID": "${XERO_CLIENT_ID}"
      }
    },
    {
      "name": "meta_social",
      "command": "node",
      "args": ["/path/to/meta_social_mcp/index.js"],
      "env": {
        "FACEBOOK_ACCESS_TOKEN": "${FACEBOOK_ACCESS_TOKEN}"
      }
    },
    {
      "name": "twitter",
      "command": "node",
      "args": ["/path/to/twitter_mcp/index.js"],
      "env": {
        "TWITTER_API_KEY": "${TWITTER_API_KEY}"
      }
    }
  ]
}
```

**Verification Criteria**:
- [ ] `mcp_config.json` exists
- [ ] All 5 servers configured with valid JSON
- [ ] Each server has: name, command, args, env
- [ ] Environment variables reference correct tokens
- [ ] MCP servers can start without errors
- [ ] Setup_Verify.py validates JSON + server count

---

### 7. Error Recovery & Graceful Degradation (GOLD - G8)

**Purpose**: System resilience when components fail

**Error Categories**:

| Category | Examples | Recovery Strategy |
|---|---|---|
| **Transient** | Network timeout, API rate limit | Exponential backoff retry (3 attempts) |
| **Authentication** | Expired token, revoked access | Alert human, pause operations, log error |
| **Logic** | Claude misinterprets message | Human review queue in `/vault/Needs_Review/` |
| **Data** | Corrupted file, missing field | Quarantine + alert, don't process |
| **System** | Orchestrator crash, disk full | Watchdog restarts, alert human |

**Technical Implementation**:

#### 7.1 Retry Handler (`utils/retry_handler.py`)

```python
def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    """Decorator for retrying transient failures"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f'Attempt {attempt+1} failed, retrying in {delay}s')
                    time.sleep(delay)
        return wrapper
    return decorator
```

**Transient Errors**:
- Network timeout
- API rate limit (429)
- Temporary service unavailable (503)
- Connection reset

**Non-Transient Errors**:
- 401 Unauthorized (token expired)
- 403 Forbidden (permission denied)
- 404 Not Found
- Invalid data format

#### 7.2 Watchdog Process (`scripts/watchdog.py`)

Monitors critical processes + auto-restarts:

**Processes to Monitor**:
1. `orchestrator.py` - Main coordination engine
2. `gmail_watcher.py` - Email monitoring
3. `whatsapp_watcher.py` - WhatsApp monitoring
4. `linkedin_watcher.py` - LinkedIn monitoring
5. `weekly_audit.py` - Scheduled briefing

**Watchdog Logic**:
```python
PROCESSES = {
    'orchestrator': 'python orchestrator.py',
    'gmail_watcher': 'python gmail_watcher.py',
    'whatsapp_watcher': 'python whatsapp_watcher.py',
    'linkedin_watcher': 'python linkedin_watcher.py',
    'weekly_audit': 'python weekly_audit.py'
}

def check_and_restart():
    for name, cmd in PROCESSES.items():
        pid_file = Path(f'/tmp/{name}.pid')
        if not is_process_running(pid_file):
            logger.warning(f'{name} not running, restarting...')
            proc = subprocess.Popen(cmd.split())
            pid_file.write_text(str(proc.pid))
            notify_human(f'{name} was restarted')

while True:
    check_and_restart()
    time.sleep(60)  # Check every minute
```

#### 7.3 Graceful Degradation Strategy

**When Gmail API is down**:
- Continue queueing other watchers
- Queue outgoing emails locally
- Retry when API restored

**When Xero connection lost**:
- Never retry payments automatically
- Require fresh human approval
- Save transaction to `/vault/Pending_Approval/`

**When Claude Code unavailable**:
- Watchers continue collecting events
- Events queue in `/vault/Inbox/`
- Process when Claude restored

**When Obsidian vault locked**:
- Write to `/tmp/` backup folder
- Sync when vault available
- Alert human of temporary issue

**Agent Skill**: `error-recovery`
- Input: Error details, context
- Output: Recovery action or human alert
- Safeguards: Never fail silently

**Verification Criteria**:
- [ ] `utils/retry_handler.py` exists with retry decorator
- [ ] `scripts/watchdog.py` exists + monitors processes
- [ ] Error logs contain recovery attempts
- [ ] System survives API downtime
- [ ] Watchdog auto-restarts failed processes
- [ ] Setup_Verify.py verifies both components

---

### 8. Comprehensive Audit Logging (GOLD - G9)

**Purpose**: Track all AI actions for compliance + debugging

**Log Format** (JSON):
```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {
    "subject": "Invoice #123",
    "body_length": 245
  },
  "approval_status": "approved",
  "approved_by": "human_user",
  "approved_at": "2026-01-07T10:25:00Z",
  "result": "success",
  "error": null,
  "execution_time_ms": 1234
}
```

**Log File Structure**:
- Location: `/vault/Logs/YYYY-MM-DD.json`
- Format: One JSON object per line (JSONL)
- Retention: Minimum 90 days
- Rotation: New file each day

**Audit Logger Implementation** (`utils/audit_logger.py`):

```python
import json
import logging
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action_type: str, target: str = None,
                   parameters: dict = None, result: str = "pending",
                   approval_status: str = None, error: str = None):
        """Log an action to daily audit file"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actor": "claude_code",
            "target": target,
            "parameters": parameters or {},
            "approval_status": approval_status,
            "result": result,
            "error": error
        }

        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{today}.json"

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
```

**Loggable Actions**:
- Email sent/received
- Payment initiated/approved/rejected
- Social media post published
- Xero transaction recorded
- HITL approval decision
- Error encountered + recovery action
- Watcher detected event
- CEO briefing generated

**Audit Rules** (`vault/Logs/audit_rules.md`):

```markdown
# Audit Rules & Retention Policy

## Required Log Fields
- timestamp (ISO 8601 UTC)
- action_type (enum)
- actor (always "claude_code" for AI actions)
- target (recipient/entity affected)
- parameters (what was done)
- approval_status (pending/approved/rejected/auto)
- result (success/failure)
- error (if failed)

## Retention Policy
- **Daily logs**: 90 days minimum
- **Monthly summaries**: 12 months
- **Sensitive actions** (payments, deletions): 1 year+
- Rotation: Archive logs older than 90 days to `/vault/Logs/archive/`

## Query Examples
- All payments from a vendor: grep "vendor_name" *.json
- Failed actions: grep '"result": "failure"' *.json
- HITL approvals: grep '"approval_status"' *.json
```

**Agent Skill**: `audit-logging`
- Input: Action details
- Output: Log entry written + confirmed
- Safeguards: Never lose audit trail

**Verification Criteria**:
- [ ] `utils/audit_logger.py` exists + functional
- [ ] `/vault/Logs/` directory exists
- [ ] Daily log files created in YYYY-MM-DD.json format
- [ ] Each log entry is valid JSON
- [ ] Log files contain required fields
- [ ] Setup_Verify.py verifies logger exists + recent logs valid

---

### 9. Agent Skills Architecture (All Tiers)

**Concept**: All AI functionality exposed as reusable Claude Code Agent Skills

**Agent Skills** are CLI commands that Claude Code executes to perform specific AI tasks. Each skill is a self-contained, documented capability.

**Bronze Tier Skills** (minimum 3):
1. `email-monitor` - Gmail watching + inbox processing
2. `filesystem-monitor` - Drop folder monitoring
3. `basic-reasoning` - Plan.md file creation

**Silver Tier Skills** (minimum 6):
- All Bronze skills +
- `whatsapp-monitor` - WhatsApp message handling
- `linkedin-automation` - LinkedIn posting + monitoring
- `request-approval` - HITL workflow management
- `email-integration` - Email MCP server usage
- `reasoning-loop` - Enhanced planning with Claude loop

**Gold Tier Skills** (minimum 9):
- All Silver skills +
- `xero-integration` - Accounting operations
- `social-post` - Facebook/Instagram/Twitter posting
- `social-summary` - Engagement report generation
- `ceo-briefing` - Weekly audit + briefing generation
- `error-recovery` - Graceful degradation handling
- `audit-logging` - Comprehensive action logging
- `orchestration-master` - Cross-domain coordination
- `request-approval` (enhanced) - Advanced HITL
- `weekly-scheduler` - Cron job management

**Skill File Structure** (`skills/[skill-name].md`):

```markdown
# Skill: [Skill Name]

## Purpose
[One-line description of what this skill does]

## Invocation
\`\`\`bash
claude-code --skill [skill-name] --context "context info"
\`\`\`

## Inputs
- `parameter1` (type): Description
- `parameter2` (type): Description

## Outputs
- `result1`: Description
- `result2`: Description

## Example
\`\`\`
Input: {email with "urgent" in subject}
Output: Action file created in /vault/Needs_Action/
\`\`\`

## Implementation
Location: `skills/[skill-name]/implementation.py`
Trigger: Watcher detects event OR scheduled
Logic: [Brief description of logic]

## Safety Constraints
- HITL required for: [actions]
- Rate limit: [limit]
- Approval threshold: [amount]

## Logs
- All actions logged to `/vault/Logs/YYYY-MM-DD.json`
- Error recovery: [strategy]

## Testing
- Unit tests: `tests/test_[skill-name].py`
- Integration test: [steps]
```

**Verification Criteria**:
- [ ] All 9 Gold skill files exist in `/skills/`
- [ ] Each skill has standard structure + all required sections
- [ ] Skill names match those in agent prompts
- [ ] All AI operations reference corresponding skill
- [ ] Setup_Verify.py counts skill files + verifies format

---

### 10. Orchestration System (Full Cross-Domain Integration)

**Purpose**: Coordinate all watchers, skills, MCP servers, and approval workflows

**Main Orchestrator** (`scripts/orchestrator.py`):

**Responsibilities**:
1. Start/monitor all watcher processes
2. Watch vault folders for changes:
   - `/vault/Inbox/` - New items from watchers
   - `/vault/Approved/` - Human-approved actions
   - `/vault/Done/` - Completed actions for archiving
3. Trigger Claude Code for processing
4. Execute MCP server actions
5. Manage approval workflows
6. Log all events to audit trail

**Flow**:

```
Watcher detects event
    ↓
Creates file in /Inbox/
    ↓
Orchestrator detects new file
    ↓
Triggers Claude Code: "Process /Inbox/ items"
    ↓
Claude reads file + creates Plan.md
    ↓
Claude needs external action (email, payment, post)
    ↓
[Sensitive?] → YES → Create /Pending_Approval/ file
                     ↓
                     Human reviews + moves to /Approved/
                     ↓
                     Orchestrator detects /Approved/ file
                     ↓
                     Calls appropriate MCP server
                     ↓
                     Logs result to audit trail
                     ↓
                     Moves to /Done/
            → NO  → Call MCP server directly
                    ↓
                    Log result
                    ↓
                    Move to /Done/
```

**Configuration** (`vault/Company_Handbook.md`):

```markdown
# Company Handbook - Rules of Engagement

## Automation Rules

### Email Handling
- Auto-reply to urgent emails from known contacts
- Flag new contact emails for human review
- Archive processed emails after 48 hours

### Payments
- Auto-approve: Recurring bills < $50
- HITL required: New payees, payments > $100
- Always: Log transaction to Xero

### Social Media
- Auto-post: Scheduled content from library
- HITL required: Real-time replies, mentions
- Always: Log engagement metrics

### Financial Actions
- All Xero transactions logged + auditable
- Weekly audit: Sunday 11 PM
- CEO Briefing: Sunday → Monday morning

## Escalation Thresholds
- Revenue decision > $5,000: Email human
- Critical error: Pause system + alert
- New vendor: Request human approval
```

**Verification Criteria**:
- [ ] `scripts/orchestrator.py` exists + runs without errors
- [ ] `vault/Company_Handbook.md` exists + defines rules
- [ ] Orchestrator successfully detects folder changes
- [ ] MCP actions execute when approved
- [ ] HITL workflow functions end-to-end
- [ ] All actions logged + auditable
- [ ] Setup_Verify.py verifies orchestrator + handbook

---

## Part III: Folder Structure & File Organization

```
DigitalFTE/
│
├── GOLD_SPEC.md ........................ ← This specification
├── Dashboard.md ........................ Progress tracking
├── Setup_Verify.py ..................... Validation script
├── README.md ........................... Setup instructions
├── ARCHITECTURE.md ..................... System design doc
├── LESSONS_LEARNED.md .................. Post-hackathon reflection
├── .env ................................ Credentials (gitignored)
├── .gitignore .......................... Exclude sensitive files
├── requirements.txt .................... Python dependencies
├── package.json ........................ Node.js dependencies
├── mcp_config.json ..................... MCP server configuration
│
├── vault/ ............................. Obsidian Vault
│   ├── Dashboard.md .................... Real-time system status
│   ├── Company_Handbook.md ............ Rules of engagement
│   ├── Business_Goals.md .............. Objectives + KPIs
│   │
│   ├── Inbox/ ......................... ← Watcher input
│   │   ├── EMAIL_[ID].md .............. From Gmail watcher
│   │   ├── WHATSAPP_[ID].md .......... From WhatsApp watcher
│   │   └── FILE_[NAME].md ............ From filesystem watcher
│   │
│   ├── Needs_Action/ .................. ← Processed by Claude
│   │   ├── TASK_[ID].md
│   │   └── ... (items requiring action)
│   │
│   ├── Plans/ ......................... ← Claude's reasoning
│   │   └── PLAN_[OBJECTIVE]_[ID].md . Reasoning + next steps
│   │
│   ├── Pending_Approval/ .............. ← Awaiting human decision
│   │   ├── PAYMENT_[DETAILS]_[ID].md
│   │   ├── EMAIL_[DETAILS]_[ID].md
│   │   └── POST_[DETAILS]_[ID].md
│   │
│   ├── Approved/ ...................... ← Ready for execution
│   │   └── [ACTION]_[ID].md .......... Approved by human
│   │
│   ├── Rejected/ ...................... ← Declined actions
│   │   └── [ACTION]_[ID].md .......... With human notes
│   │
│   ├── Done/ .......................... ← Completed + archived
│   │   └── [TYPE]_[ID].md ............ Completed action
│   │
│   ├── Accounting/ .................... Financial data
│   │   ├── xero_config.md ............ Xero org details
│   │   ├── Current_Month.md .......... Transaction log
│   │   ├── Rates.md .................. Billing rates
│   │   └── invoices/ ................. Generated invoices
│   │
│   ├── Briefings/ .................... CEO briefings
│   │   └── 2026-01-06_briefing.md ... Sunday → Monday
│   │
│   ├── Social_Media/ ................. Social content
│   │   ├── posting_schedule.md ....... Content calendar
│   │   ├── content_library.md ........ Reusable templates
│   │   └── engagement_summary.md .... Weekly analytics
│   │
│   └── Logs/ .......................... Audit trail
│       ├── 2026-01-07.json ........... Daily log file
│       ├── audit_rules.md ............ Logging policy
│       ├── error_recovery.md ......... Error handling
│       └── archive/ .................. Old logs (90+ days)
│
├── watchers/ ......................... Perception layer
│   ├── base_watcher.py ............... Abstract base class
│   ├── gmail_watcher.py .............. Gmail polling
│   ├── whatsapp_watcher.py ........... WhatsApp automation
│   ├── linkedin_watcher.py ........... LinkedIn API
│   ├── filesystem_watcher.py ......... Drop folder monitor
│   └── watcher_manager.py ............ Process manager
│
├── scripts/ .......................... Orchestration
│   ├── orchestrator.py ............... Main coordination engine
│   ├── watchdog.py ................... Process health monitor
│   └── weekly_audit.py ............... CEO briefing generator
│
├── mcp_servers/ ...................... External action handlers
│   ├── email_mcp/
│   │   ├── index.js ................. Email MCP implementation
│   │   └── package.json ............. Dependencies
│   ├── browser_mcp/
│   │   ├── index.js ................. Browser automation
│   │   └── package.json
│   ├── xero_mcp/
│   │   ├── index.js ................. Xero accounting
│   │   └── package.json
│   ├── meta_social_mcp/
│   │   ├── index.js ................. Facebook/Instagram
│   │   └── package.json
│   └── twitter_mcp/
│       ├── index.js ................. Twitter/X posting
│       └── package.json
│
├── utils/ ........................... Shared utilities
│   ├── retry_handler.py ............. Exponential backoff
│   ├── audit_logger.py .............. Logging system
│   ├── config_loader.py ............. Config management
│   └── error_handler.py ............. Error management
│
├── skills/ .......................... Claude Code Agent Skills
│   ├── email-monitor.md
│   ├── whatsapp-monitor.md
│   ├── linkedin-automation.md
│   ├── xero-integration.md
│   ├── social-post.md
│   ├── social-summary.md
│   ├── ceo-briefing.md
│   ├── request-approval.md
│   └── error-recovery.md
│
└── tests/ ........................... Unit + integration tests
    ├── test_watchers.py
    ├── test_orchestrator.py
    ├── test_mcp_servers.py
    └── test_error_recovery.py
```

---

## Part IV: Implementation Roadmap

### Phase 1: Specification (This Document)
- ✅ Map all requirements to components
- ✅ Define technical architecture
- ✅ Specify folder structure
- ✅ Create verification criteria

### Phase 2: Scaffolding
- Create all vault folders
- Create template files
- Initialize config files

### Phase 3: Dashboard
- Create progress tracking dashboard
- Set up tier checkboxes
- Plan demo script

### Phase 4: Validation Script
- Implement Setup_Verify.py
- Run verification → expect ~30-40% score (Bronze foundation)

### Phase 5: Account Setup
- Create Xero account + OAuth app
- Create Meta Business account + developer app
- Create Twitter/X developer account
- Set up Gmail API + Google Cloud project
- Link WhatsApp Web session

### Phase 6: Watcher Implementation
- Build base_watcher.py base class
- Implement gmail_watcher.py
- Implement whatsapp_watcher.py
- Implement linkedin_watcher.py
- Implement filesystem_watcher.py
- Set up PM2 for process management

### Phase 7: MCP Server Setup
- Configure email MCP (Gmail)
- Configure browser MCP (Playwright)
- Build/configure xero_mcp
- Build/configure meta_social_mcp
- Build/configure twitter_mcp
- Test all servers → expect +30% score improvement

### Phase 8: Agent Skills Definition
- Create all 9 skill definition files
- Document each skill with examples
- Implement corresponding skill logic

### Phase 9: Orchestration
- Build scripts/orchestrator.py
- Implement folder watching logic
- Test HITL workflow end-to-end
- Build error recovery + graceful degradation

### Phase 10: CEO Briefing System
- Build weekly_audit.py
- Create cron job (Sunday 11 PM)
- Generate first briefing
- Integrate with Xero for financial data

### Phase 11: Testing & Polish
- Write unit tests for all components
- Integration testing (full flows)
- Load testing (process stability)
- Security audit (credential handling)

### Phase 12: Documentation & Demo
- Write README.md (setup steps)
- Write ARCHITECTURE.md (design details)
- Create demo video (5-10 min)
- Update LESSONS_LEARNED.md
- Final verification: Setup_Verify.py → expect 95%+ score

---

## Part V: Verification Checklist

### Before Starting Implementation
- [ ] All prerequisites installed (Python 3.13+, Node.js, Obsidian, Claude Code)
- [ ] Read entire GOLD_SPEC.md
- [ ] Understand folder structure + naming conventions
- [ ] Review all 10 Gold requirements
- [ ] Create .env file (placeholder)
- [ ] Create .gitignore with secrets

### After Phase 2 (Scaffolding)
- [ ] All folders created with correct names
- [ ] Template files exist
- [ ] Setup_Verify.py runs successfully
- [ ] Score: 30-40% (Bronze foundation)

### After Phase 4 (Dashboard)
- [ ] Dashboard.md created + readable
- [ ] All tiers have checklist items
- [ ] Demo script outlined

### After Phase 7 (MCP Setup)
- [ ] All 5 MCP servers in config
- [ ] Each server has valid configuration
- [ ] Credentials in .env file
- [ ] Setup_Verify.py score: 50-60%

### After Phase 10 (CEO Briefing)
- [ ] First briefing generated successfully
- [ ] Cron/Task Scheduler configured
- [ ] Briefing includes all required sections
- [ ] Integrated with Xero data

### Before Final Demo
- [ ] Setup_Verify.py score: 95%+ (Gold ready)
- [ ] All 9 Gold requirements working
- [ ] Demo video recorded (5-10 min)
- [ ] GitHub repo updated with all code
- [ ] README.md + ARCHITECTURE.md complete
- [ ] All credentials safely stored in .env (gitignored)

---

## Part VI: Success Criteria

**Gold Tier Completion = ALL of the following:**

1. ✅ Vault structure: 100% (all folders created)
2. ✅ Configuration: 100% (GOLD_SPEC.md + Dashboard.md + Setup_Verify.py)
3. ✅ Watchers: 100% (5 watchers functional + PM2 managed)
4. ✅ MCP Servers: 100% (5 servers configured + authenticated)
5. ✅ Agent Skills: 100% (9 skill files with implementation)
6. ✅ HITL Workflow: 100% (approval folders + orchestrator working)
7. ✅ CEO Briefing: 100% (runs Sunday 11 PM, generates briefing)
8. ✅ Error Recovery: 100% (retry handler + watchdog operational)
9. ✅ Audit Logging: 100% (daily logs in JSON, 90-day retention)
10. ✅ Documentation: 100% (README + ARCHITECTURE + demo video)
11. ✅ Setup_Verify.py Score: 95%+ (Gold readiness confirmed)
12. ✅ Wednesday Demo: Live system demo showing all Gold features

---

## References

**Hackathon Document**: `/Users/hparacha/DigitalFTE/Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`

**API Documentation**:
- Gmail API: https://developers.google.com/gmail/api/
- Xero API: https://developer.xero.com/
- Meta API: https://developers.facebook.com/
- Twitter API: https://developer.twitter.com/

**Libraries**:
- Playwright (browser automation)
- google-auth-oauthlib (Gmail)
- xero-python (Xero SDK)
- tweepy (Twitter API)

---

**GOLD_SPEC.md Created**: 2026-01-08
**Status**: Ready for Phase 2 Implementation
