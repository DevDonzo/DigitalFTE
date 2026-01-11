# Demo Script - Digital FTE GOLD Tier

**Duration**: 5-10 minutes
**Focus**: Show autonomous AI employee in action

---

## Demo Outline

### 1. Architecture Overview (1 min)
- Show folder structure: vault/Inbox → Plans → Approved → Done
- Explain data flow: External input → Watcher → Claude reasoning → Action → Logged

### 2. Email Monitoring (1.5 min)
```bash
# Show Gmail watcher running
python watchers/gmail_watcher.py &

# Send test email (from phone/browser)
# Watch it appear in vault/Inbox/ as EMAIL_*.md

# Show file structure
cat vault/Inbox/EMAIL_*.md
```

### 3. Orchestrator Processing (1.5 min)
```bash
# Start orchestrator
python scripts/orchestrator.py &

# Watch it:
# - Detect email in /Inbox/
# - Create reasoning in /Plans/
# - Check if needs approval
# - Move to /Pending_Approval/ or execute directly

tail -f vault/Logs/*.json
```

### 4. Human-in-the-Loop (1 min)
```bash
# Show approval workflow
ls vault/Pending_Approval/    # Files waiting for human

# Simulate human approval
mv vault/Pending_Approval/*.md vault/Approved/

# Orchestrator immediately executes
ls vault/Done/               # Action completed
```

### 5. CEO Briefing (1 min)
```bash
# Generate weekly business briefing
python scripts/weekly_audit.py

# Show generated briefing
cat vault/Briefings/*.md
```

### 6. Audit Trail (1 min)
```bash
# Show all actions logged
cat vault/Logs/2026-01-*.json | jq .

# Every action tracked:
# - Who (orchestrator/watcher)
# - What (action type)
# - When (timestamp)
# - Result (success/failure)
```

### 7. System Status (1 min)
```bash
# Show dashboard
cat vault/Dashboard.md

# Verify all components
python Setup_Verify.py

# Check requirements coverage
cat GOLD_COMPLIANCE.md
```

---

## Demo Flow (Actual Execution)

1. **Pre-setup** (do before demo):
   ```bash
   # Start all services
   python watchers/gmail_watcher.py &
   python watchers/filesystem_watcher.py &
   python scripts/orchestrator.py &
   
   # Monitor
   tail -f vault/Logs/*.json
   ```

2. **During demo**:
   - Send test email / drop file / WhatsApp message
   - Watch system process automatically
   - Show each stage with file operations
   - Demonstrate approval workflow
   - Show generated briefing

3. **Key talking points**:
   - "This AI employee works 24/7"
   - "Every action is logged for compliance"
   - "Humans stay in control via HITL"
   - "It learns from rules in Company_Handbook.md"
   - "Xero integration for accounting"
   - "Social media posting to 4 platforms"

---

## Video Recording Tips

- Record 5-10 min total
- Show terminal + file system
- Speed up slow parts (2x)
- Add text overlays for clarity
- Show real results (generated files, logs)

---

## Success Criteria

✅ Watcher detects incoming event (email/message/file)
✅ Orchestrator processes and creates plan
✅ Approval workflow functions
✅ CEO briefing generates with metrics
✅ Audit trail shows all actions
✅ System handles errors gracefully
✅ All GOLD tier features visible

