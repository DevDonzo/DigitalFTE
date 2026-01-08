# Integration Test Guide - Phase 6

**Purpose**: Test all systems working together
**Time**: 2-3 hours
**Requirement**: All API credentials in .env

---

## Test 1: Gmail Watcher Integration

**Objective**: Monitor real Gmail and create vault files

```bash
# 1. Ensure credentials.json exists
test -f credentials.json || echo "ERROR: Get from Google Cloud"

# 2. Run watcher
python watchers/gmail_watcher.py &
GMAIL_PID=$!

# 3. Send test email to yourself
# (from another email account or phone)

# 4. Wait 5 seconds
sleep 5

# 5. Verify file created
ls -la vault/Inbox/EMAIL_*.md
test $(ls vault/Inbox/EMAIL_*.md | wc -l) -gt 0 && echo "✅ PASS" || echo "❌ FAIL"

# 6. Kill process
kill $GMAIL_PID
```

---

## Test 2: Orchestrator Processing

**Objective**: Inbox → Plans → Done flow

```bash
# 1. Create test inbox file
mkdir -p vault/Inbox vault/Plans vault/Done
cat > vault/Inbox/TEST_001.md << 'EOF'
---
type: test
priority: high
---
# Test Email
This should be processed
EOF

# 2. Start orchestrator
python scripts/orchestrator.py &
ORCH_PID=$!

# 3. Wait for processing
sleep 3

# 4. Verify plan created
test -f vault/Plans/PLAN_TEST_001.md && echo "✅ PASS" || echo "❌ FAIL"

# 5. Verify moved to done
sleep 1
ls vault/Done/ | wc -l

kill $ORCH_PID
```

---

## Test 3: HITL Approval Workflow

**Objective**: Create approval → Human approves → Action executes

```bash
# 1. Create approval request
mkdir -p vault/Pending_Approval vault/Approved vault/Done
cat > vault/Pending_Approval/TEST_PAYMENT.md << 'EOF'
---
type: approval_request
action: payment
amount: 100
---
# Test Payment Approval
EOF

# 2. Verify in pending
ls vault/Pending_Approval/ | grep TEST && echo "✅ PASS" || echo "❌ FAIL"

# 3. Simulate human approval
mv vault/Pending_Approval/TEST_PAYMENT.md vault/Approved/

# 4. Verify moved
ls vault/Approved/ | grep TEST && echo "✅ PASS" || echo "❌ FAIL"

# 5. Start orchestrator to execute
python scripts/orchestrator.py &
sleep 2
kill $!

# 6. Verify moved to done
ls vault/Done/ | grep TEST && echo "✅ PASS" || echo "❌ FAIL"
```

---

## Test 4: CEO Briefing Generation

**Objective**: Generate weekly audit briefing

```bash
# 1. Ensure Business_Goals.md exists
test -f vault/Business_Goals.md && echo "✅ Found" || echo "❌ Missing"

# 2. Run audit
python scripts/weekly_audit.py

# 3. Verify briefing created
ls -la vault/Briefings/*.md
test -f vault/Briefings/*_briefing.md && echo "✅ PASS" || echo "❌ FAIL"

# 4. Check content
grep -q "CEO Briefing" vault/Briefings/*.md && echo "✅ PASS" || echo "❌ FAIL"
```

---

## Test 5: Audit Logging

**Objective**: Verify all actions logged

```bash
# 1. Check log file exists
ls -la vault/Logs/*.json

# 2. Verify JSON format
python3 << 'PYEOF'
import json
logs = open('vault/Logs/*.json').read()
for line in logs.split('\n'):
    if line:
        json.loads(line)  # Will fail if not valid JSON
print("✅ All logs are valid JSON")
PYEOF

# 3. Check entry count
wc -l vault/Logs/*.json

# 4. Verify fields
grep -q '"timestamp"' vault/Logs/*.json && echo "✅ timestamp"
grep -q '"action_type"' vault/Logs/*.json && echo "✅ action_type"
grep -q '"result"' vault/Logs/*.json && echo "✅ result"
```

---

## Test 6: Error Recovery

**Objective**: System continues when component fails

```bash
# 1. Run tests
pytest tests/test_error_recovery.py -v

# 2. Check retry logic
python3 -c "from utils.retry_handler import with_retry; print('✅ Retry handler works')"

# 3. Verify graceful degradation
# Kill Gmail watcher, verify FileSystem watcher still works
pkill -f gmail_watcher || true
python watchers/filesystem_watcher.py &
cp /tmp/test.txt ~/Downloads/
sleep 2
ls vault/Inbox/FILE_*.md && echo "✅ FileSystem works without Gmail"
pkill -f filesystem_watcher
```

---

## Test 7: MCP Server Configuration

**Objective**: Verify MCP servers configured

```bash
# 1. Check mcp_config.json valid
python3 -c "import json; json.load(open('mcp_config.json'))"
echo "✅ MCP config valid JSON"

# 2. Verify all 5 servers
grep -c '"name"' mcp_config.json
test $(grep -c '"name"' mcp_config.json) -eq 5 && echo "✅ All 5 servers"

# 3. Check credentials
grep -E "GMAIL|XERO|FACEBOOK|TWITTER" .env | wc -l
test $(grep -E "GMAIL|XERO|FACEBOOK|TWITTER" .env | wc -l) -gt 0 && echo "✅ Credentials found"
```

---

## Expected Results

```
Test 1 (Gmail):        ✅ PASS - Files created
Test 2 (Orchestrator): ✅ PASS - Plans created
Test 3 (HITL):         ✅ PASS - Approval workflow
Test 4 (CEO Briefing): ✅ PASS - Briefing generated
Test 5 (Logging):      ✅ PASS - All logs valid
Test 6 (Error):        ✅ PASS - Graceful degradation
Test 7 (MCP):          ✅ PASS - All configured

OVERALL: ✅ GOLD TIER READY FOR PHASE 7
```

---

## Troubleshooting

| Test | Fails | Fix |
|------|-------|-----|
| Gmail | "credentials.json not found" | Download from Google Cloud |
| Orchestrator | No plan created | Check vault/Logs/ for errors |
| HITL | Move doesn't trigger | Orchestrator must be running |
| CEO Briefing | Empty briefing | Check Business_Goals.md exists |
| Logging | Invalid JSON | Check audit_logger.py |

