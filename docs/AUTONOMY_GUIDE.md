# 🤖 COMPLETE AUTONOMY GUIDE - How Everything Works

This explains exactly how your Digital FTE runs 24/7 without human intervention (except approvals).

---

## 🎯 The Big Picture: 5 Autonomous Loops

```
┌─────────────────────────────────────────────────────────────┐
│  LOOP 1: PERCEPTION (Watchers)                              │
│  Gmail Watcher  [20s]  ─────────────────┐                   │
│  WhatsApp Watcher [10s] ────────────────┤──> vault/Inbox/  │
│  LinkedIn Watcher [5m] ─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LOOP 2: REASONING (Orchestrator)                           │
│  Watches vault/Needs_Action/ [2s polling]                   │
│  ├─ Email Drafter (OpenAI)                                  │
│  ├─ WhatsApp Drafter (OpenAI)                               │
│  └─ Tweet Drafter (OpenAI)                                  │
│  Creates vault/Pending_Approval/ files                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LOOP 3: HUMAN-IN-THE-LOOP (You)                            │
│  Open Obsidian, review vault/Pending_Approval/              │
│  ├─ Edit if needed                                          │
│  └─ Move to vault/Approved/ to execute                      │
│  (Or delete to reject)                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LOOP 4: EXECUTION (Orchestrator + MCP Servers)             │
│  Watches vault/Approved/ [2s polling]                       │
│  ├─ Send email via Gmail API                                │
│  ├─ Send WhatsApp via Twilio                                │
│  ├─ Post to LinkedIn/Twitter/Facebook/Instagram             │
│  └─ Log results to vault/Logs/                              │
│  Moves to vault/Done/                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LOOP 5: RESILIENCE (Watchdog)                              │
│  Monitors [30s] all processes:                              │
│  ├─ orchestrator.py                                         │
│  ├─ gmail_watcher.py                                        │
│  ├─ whatsapp_watcher.py                                     │
│  ├─ linkedin_watcher.py                                     │
│  └─ webhook_server.py                                       │
│  Auto-restart if crash (3-5 second recovery)                │
└─────────────────────────────────────────────────────────────┘

BONUS LOOP: CEO Briefing (Scheduled)
└─> Runs every Monday 8:00 AM (macOS launchd)
    Pulls Xero + logs + vault data
    Generates vault/Briefings/
```

---

## 🔄 LOOP 1: PERCEPTION LAYER (Watchers)

### How Watchers Work

**Gmail Watcher** (`watchers/gmail_watcher.py`):
```python
class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path, credentials_path):
        super().__init__(vault_path, check_interval=20)  # Polls every 20 seconds
        self.service = self._authenticate()  # Uses credentials.json
    
    def check_for_updates(self):
        # Every 20 seconds: ask Gmail for unread important emails
        results = self.service.users().messages().list(
            userId='me', q='is:unread is:important', maxResults=5
        ).execute()
        return new_emails  # Return only emails we haven't seen before
```

**When It Runs**: Continuously (daemonized by watchdog.py)
- Starts at system boot (via watchdog)
- Polls Gmail API every 20 seconds
- When new email found → creates file in `vault/Inbox/EMAIL_*.md`

**Where Code**: `/Users/hparacha/DigitalFTE/watchers/gmail_watcher.py` (line 62-75)

**Output**: 
```
vault/Inbox/EMAIL_hparacha_20260111_120000.md
---
from: client@example.com
subject: Project Update
body: [email content]
---
```

---

### Similar for WhatsApp & LinkedIn

**WhatsApp Watcher**:
- Polls every 10 seconds
- Receives messages via Twilio webhook (NOT polling)
- Creates file in `vault/Inbox/WHATSAPP_*.md`

**LinkedIn Watcher**:
- Polls every 5 minutes
- Checks for notifications, messages, comments
- Creates file in `vault/Inbox/LINKEDIN_*.md`

---

## 🧠 LOOP 2: REASONING LAYER (Orchestrator)

### How Orchestrator Works

**Main Process** (`scripts/orchestrator.py`):
```python
class VaultHandler(FileSystemEventHandler):
    def __init__(self, vault_path):
        self.vault = Path(vault_path)
        self.inbox = self.vault / 'Inbox'           # Input
        self.needs_action = self.vault / 'Needs_Action'     # Processing
        self.pending = self.vault / 'Pending_Approval'      # Waiting for you
        self.approved = self.vault / 'Approved'   # Ready to execute
        self.done = self.vault / 'Done'           # Completed
    
    def on_created(self, event):
        # Called when ANY file is created/modified in vault
        # Decides what to do based on folder
        
        if file_is_in(self.inbox):
            # New email/WhatsApp/LinkedIn detected
            # Step 1: AI drafts response
            draft = self.email_drafter.draft_reply(file)
            # Step 2: Create in Pending_Approval/
            # (waits for human approval)
        
        elif file_is_in(self.approved):
            # You moved file here - time to execute!
            # Call appropriate MCP server to send/post
            self._call_meta_api(content)  # Facebook/Instagram
            # Move to Done/
```

**Uses watchdog Library**:
```python
observer = Observer()
observer.schedule(handler, str(vault_path), recursive=True)
observer.start()
while True:
    time.sleep(1)  # Watches folders for changes
```

**When It Runs**: Continuously at startup
- Starts at system boot (via watchdog.py)
- Watches all vault folders
- Responds to file creation/modification in <100ms

**Where Code**: `/Users/hparacha/DigitalFTE/scripts/orchestrator.py` (line 844-900)

---

## 📝 LOOP 3: HUMAN-IN-THE-LOOP (You)

### How Approval Works

**You**:
1. Open Obsidian
2. Go to `vault/Pending_Approval/`
3. See files like `EMAIL_DRAFT_20260111_120000.md`
4. Review AI's draft response
5. Choose:
   - **Keep it**: Move to `vault/Approved/`
   - **Edit it**: Change text, then move to `Approved/`
   - **Reject it**: Delete it or move to `Rejected/`

**That's IT!** No manual triggering needed. Orchestrator watches and auto-executes.

---

## ⚡ LOOP 4: EXECUTION LAYER (MCP Servers)

### How Execution Works

When file enters `vault/Approved/`:

```python
def on_modified(self, event):
    if file_is_in(self.approved):
        # Read the file
        content = file.read_text()
        
        # Determine action type
        if "EMAIL" in filename:
            self._call_email_mcp(to, subject, body)
        elif "WHATSAPP" in filename:
            self._call_whatsapp_api(phone, message)
        elif "LINKEDIN" in filename:
            self._call_linkedin_api(text)
        elif "FACEBOOK" in filename:
            self._call_meta_api(text)  # Meta Social MCP
        elif "TWITTER" in filename:
            self._call_twitter_api(tweet_text)
        
        # Move to Done/
        file.move(self.done)
```

**MCP Servers Handle Real Actions**:
- `mcp_servers/email_mcp/` → Gmail API
- `mcp_servers/meta_social_mcp/` → Facebook/Instagram API
- `mcp_servers/twitter_mcp/` → Twitter API
- `mcp_servers/xero_mcp/` → Xero accounting API

**Where Code**: `/Users/hparacha/DigitalFTE/scripts/orchestrator.py` (line 564-672)

---

## 🛡️ LOOP 5: RESILIENCE (Watchdog)

### How Watchdog Keeps Everything Alive

**Watchdog Process** (`scripts/watchdog.py`):
```python
PROCESSES = {
    'orchestrator': {
        'cmd': 'python3 scripts/orchestrator.py',
        'pid_file': '/tmp/digitalfte_orchestrator.pid',
        'restart_delay': 5,
        'max_restarts': 10,
    },
    'gmail_watcher': {
        'cmd': 'python3 watchers/gmail_watcher.py',
        'restart_delay': 3,
    },
    # ... 4 more processes
}

while True:
    for name, config in PROCESSES.items():
        pid = get_process_pid(name)
        
        if pid is None or not is_running(pid):
            # Process crashed!
            logger.error(f"Restarting {name}...")
            start_process(name)
        
        time.sleep(30)  # Check every 30 seconds
```

**When It Runs**:
- Starts at system boot (via `com.digitalfte.watchdog.plist`)
- Checks every 30 seconds
- If any process crashed, restarts in 3-5 seconds

**Startup**:
```bash
# Enable it (runs on boot):
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist

# Or test manually:
python3 scripts/watchdog.py
```

---

## 📅 BONUS: CEO BRIEFING LOOP (Scheduled)

### How Morning Briefing Works

**Scheduled Execution** (`scripts/schedule_ceo_briefing.plist`):
```xml
<StartCalendarInterval>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>        <!-- Monday -->
        <key>Hour</key>
        <integer>8</integer>        <!-- 8:00 AM -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</StartCalendarInterval>
```

**Every Monday at 8 AM**:
```python
def generate_ceo_briefing():
    # Gather metrics
    emails_sent = count_emails_sent(vault, week_start)
    tasks_completed = count_completed_tasks(vault)
    
    # Get Xero financials
    xero_data = get_xero_financials()  # Real accounting data!
    revenue_this_week = xero_data['revenue']
    
    # Build report
    briefing = f"""
    # Monday Morning CEO Briefing
    
    Revenue this week: ${revenue_this_week}
    Emails processed: {emails_sent}
    Tasks completed: {tasks_completed}
    
    Recommendations:
    - Focus on X
    - Opportunity in Y
    """
    
    # Save to vault
    save_to_vault(briefing, f'vault/Briefings/{date}_briefing.md')
```

**Where Code**: `/Users/hparacha/DigitalFTE/scripts/weekly_audit.py` (line 31-467)

**Scheduled By**: `schedule_ceo_briefing.plist` (macOS launchd)

**Enable It**:
```bash
launchctl load ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

---

## 🎬 Real Example: Email Arrives

### Timeline (Real Events)

**8:00 AM - Email arrives**
```
Gmail Server: "New unread important email from client@example.com"
```

**8:00:05 AM - Gmail Watcher detects (within 20 seconds)**
```
gmail_watcher.py polls Gmail API
Finds new email
Creates vault/Inbox/EMAIL_client_20260111_080005.md
Logs to vault/Logs/2026-01-11.json
```

**8:00:06 AM - Orchestrator detects file**
```
orchestrator.py (watching vault/) detects new file
Reads email content
Calls EmailDrafter (OpenAI gpt-4o-mini)
OpenAI generates professional response
Creates vault/Pending_Approval/EMAIL_DRAFT_20260111_080006.md
Logs action
```

**8:00:07 AM - You wake up, open Obsidian**
```
You see new draft in vault/Pending_Approval/
You review AI response
You either:
  - Move to vault/Approved/ (auto-sends)
  - Edit text, then move to Approved/ (sends edited version)
  - Delete or reject
```

**8:00:10 AM - Orchestrator detects approval**
```
orchestrator.py sees file in vault/Approved/
Calls Gmail API (via MCP server)
Sends email reply
Moves file to vault/Done/
Logs success to vault/Logs/2026-01-11.json
```

**Result**: Email answered in < 10 seconds total (with your human review)

---

## 🚀 How to Start Everything

### Option 1: Test Manually (for debugging)

```bash
# Terminal 1 - Start orchestrator
cd /Users/hparacha/DigitalFTE
python3 scripts/orchestrator.py

# Terminal 2 - Start watchers
python3 watchers/gmail_watcher.py &
python3 watchers/whatsapp_watcher.py &
python3 watchers/linkedin_watcher.py &

# Terminal 3 - Monitor with watchdog
python3 scripts/watchdog.py
```

### Option 2: Production (Auto-Start on Boot)

```bash
# Copy plist files to Launch Agents
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/
cp scripts/schedule_ceo_briefing.plist ~/Library/LaunchAgents/

# Load them (starts now + on every boot)
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
launchctl load ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist

# Verify loaded
launchctl list | grep digitalfte
```

### Option 3: Check What's Running

```bash
# View active processes
ps aux | grep python | grep -E "(orchestrator|watcher|webhook)"

# View watchdog logs
tail -f ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
cat vault/Logs/watchdog.out

# View CEO briefing logs
cat vault/Logs/ceo_briefing.log
```

---

## 📊 THE AUTONOMY CHECKLIST

- ✅ **Watcher** polls every 20s (Gmail), 10s (WhatsApp), 5m (LinkedIn)
- ✅ **Orchestrator** watches vault every 2s, auto-drafts with AI
- ✅ **You approve** by moving files in Obsidian
- ✅ **MCP Servers** execute actions (send/post)
- ✅ **Watchdog** monitors processes, auto-restart on crash
- ✅ **CEO Briefing** runs Monday 8 AM automatically
- ✅ **All logs** tracked in vault/Logs/ for audit trail

**Bottom Line**: Once started, runs 24/7 without you touching the terminal. You only review approvals in Obsidian.

