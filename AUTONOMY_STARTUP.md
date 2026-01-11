# 🚀 ACTIVATE FULL AUTONOMY

Your Digital FTE is built but not yet autonomous. These 2 commands turn it on 24/7:

## Step 1: Enable Watchdog (Process Manager)

```bash
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
```

**What this does**:
- Starts watchdog process manager on system boot
- Watchdog monitors 5 core processes (orchestrator + 4 watchers)
- If any crash, auto-restarts in 3-5 seconds
- Runs forever until you unload it

---

## Step 2: Enable CEO Briefing (Scheduler)

```bash
cp scripts/schedule_ceo_briefing.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

**What this does**:
- Every Monday at 8:00 AM, runs autonomous audit
- Pulls email/WhatsApp/LinkedIn metrics
- Fetches Xero financial data
- Generates CEO briefing to vault/Briefings/
- Zero manual intervention

---

## Step 3: Verify It's Working

```bash
# Check processes are loaded
launchctl list | grep digitalfte

# Check watchdog is running
tail -f vault/Logs/watchdog.out

# Check processes are alive
ps aux | grep python | grep -E "(orchestrator|watcher)"
```

---

## Step 4: Test the System

Send yourself a test message:

1. **Email**: Send to your Gmail
2. **WhatsApp**: Send to +14155238886 
3. **LinkedIn**: Post a comment on a post

Then:

4. Open Obsidian
5. Look in `vault/Pending_Approval/`
6. You should see AI-drafted responses
7. Move one to `vault/Approved/`
8. Watch it auto-execute and move to `vault/Done/`

---

## What's Now Autonomous

| Component | Trigger | Frequency |
|-----------|---------|-----------|
| **Gmail** | New important email | Every 20 seconds (continuous) |
| **WhatsApp** | Message via Twilio | Every 10 seconds (continuous) |
| **LinkedIn** | New notification | Every 5 minutes (continuous) |
| **Orchestrator** | File changes in vault | Real-time (<100ms) |
| **AI Drafting** | New input detected | Instant (gpt-4o-mini) |
| **HITL Approval** | You move files | Your decision |
| **Execution** | File in /Approved/ | Real-time |
| **CEO Briefing** | Calendar event | Every Monday 8:00 AM |
| **Watchdog** | Process crash | Every 30 seconds (auto-restart) |

---

## How It All Works Together

```
System Boot (or manual launchctl load)
    ↓
Watchdog starts (monitors processes)
    ├─→ Starts orchestrator.py
    ├─→ Starts gmail_watcher.py
    ├─→ Starts whatsapp_watcher.py
    ├─→ Starts linkedin_watcher.py
    └─→ Starts webhook_server.py
    
    [All 5 run in background, forever]
    [Watchdog checks every 30s, auto-restarts on crash]

Separately:
    ↓
Every Monday 8:00 AM, launchd triggers:
    ├─→ weekly_audit.py
    └─→ Pulls metrics + Xero data + generates briefing

Meanwhile, continuously:
    ↓
1. Gmail Watcher polls → finds email → creates vault/Inbox/
2. Orchestrator watches → detects file → calls AI drafter
3. AI drafts response → creates vault/Pending_Approval/
4. You review in Obsidian → move to vault/Approved/
5. Orchestrator detects approval → sends email/posts/etc
6. File moves to vault/Done/
7. Action logged to vault/Logs/YYYY-MM-DD.json

[Cycle repeats forever, unattended]
```

---

## To Stop (if needed)

```bash
launchctl unload ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
launchctl unload ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

---

## To Debug Issues

```bash
# See what's running
ps aux | grep python | grep -E "(orchestrator|watcher|webhook)"

# View watchdog logs
tail -f vault/Logs/watchdog.out

# View recent actions
tail -f vault/Logs/2026-01-11.json

# Run manually (for debugging)
python3 scripts/watchdog.py
python3 scripts/orchestrator.py

# Kill a process to test auto-restart
pkill -f "python3 scripts/orchestrator.py"
# Watch watchdog restart it within 5 seconds:
tail -f vault/Logs/watchdog.out
```

---

## TLDR

**2 commands to make it autonomous 24/7:**

```bash
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/ && \
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist

cp scripts/schedule_ceo_briefing.plist ~/Library/LaunchAgents/ && \
launchctl load ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

Then it runs forever. You only review approvals in Obsidian.

---

**Status**: Ready to activate ✅
**Next**: Run the 2 commands above
**Then**: Your Digital FTE runs 24/7 autonomously 🚀
