# Troubleshooting Guide

## Common Issues and Solutions

### Setup & Installation

#### Issue: "Python 3 required" on setup
**Cause**: Python not installed or not in PATH
**Solution**:
```bash
# Check version
python3 --version

# Install if needed (macOS)
brew install python3

# Install if needed (Ubuntu)
sudo apt-get install python3 python3-pip
```

#### Issue: "pip: command not found"
**Cause**: pip not installed with Python
**Solution**:
```bash
# Reinstall pip
python3 -m ensurepip --upgrade

# Or use system pip
sudo apt-get install python3-pip
```

#### Issue: ModuleNotFoundError during setup
**Cause**: Dependencies not installed
**Solution**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# If specific package fails, install individually
pip install google-auth-oauthlib
pip install playwright
pip install watchdog
```

---

### Credentials & Authentication

#### Issue: "Invalid credentials.json" in Gmail watcher
**Cause**: OAuth token expired or invalid
**Solution**:
1. Delete `credentials.json`
2. Delete `token.pickle`
3. Re-run Gmail watcher to trigger OAuth flow
4. Complete browser authentication
5. Restart watcher

#### Issue: "WhatsApp: QR code not scanned"
**Cause**: Browser didn't open or authentication timed out
**Solution**:
```bash
# Clear WhatsApp session
rm -rf ~/.wapp_session

# Restart watcher with timeout
python watchers/whatsapp_watcher.py --qr-timeout 120
```

#### Issue: "Xero: 401 Unauthorized"
**Cause**: API credentials invalid or expired
**Solution**:
1. Verify Client ID in `.env`
2. Verify Client Secret in `.env`
3. Check token expiration: `cat .env | grep XERO_TOKEN`
4. Re-authenticate via Xero dashboard
5. Update `.env` with new credentials

#### Issue: "Twitter API: Rate limit exceeded"
**Cause**: Too many API calls in short time
**Solution**:
1. Wait 15 minutes for rate limit reset
2. Check current limits: `GET /2/tweets/search/recent`
3. Adjust polling interval in `.env`: `TWITTER_CHECK_INTERVAL=600` (10 min)
4. Upgrade to elevated access if needed

---

### Watcher Issues

#### Issue: Email watcher crashes on startup
**Cause**: Gmail API not enabled or network issue
**Solution**:
```bash
# Check Gmail API is enabled
curl https://www.googleapis.com/gmail/v1/users/me/profile

# If error, enable in Google Cloud Console:
# APIs & Services > Library > Search "Gmail" > Enable

# Test network connection
ping google.com

# Restart watcher with verbose logging
python watchers/gmail_watcher.py --debug
```

#### Issue: Watcher runs but no files created
**Cause**: Vault path wrong or permissions issue
**Solution**:
```bash
# Verify vault path exists
ls -la vault/Inbox

# Check write permissions
touch vault/Inbox/test.md

# Check watcher config
grep VAULT_PATH .env

# Verify watcher is running
ps aux | grep gmail_watcher
```

#### Issue: WhatsApp watcher opens browser but fails
**Cause**: Playwright browser issue
**Solution**:
```bash
# Reinstall Playwright browsers
playwright install

# Update Playwright
pip install --upgrade playwright

# Check browser executable
which chromium-browser  # or /usr/bin/chromium
```

#### Issue: FileSystem watcher not detecting files
**Cause**: Watching wrong directory
**Solution**:
```bash
# Verify watched directory
grep WATCH_DIRECTORY .env

# Check file permissions
ls -la ~/Downloads

# Monitor with verbose logging
python watchers/filesystem_watcher.py --debug
```

---

### Orchestrator Issues

#### Issue: "Cannot find vault/Plans directory"
**Cause**: Directory structure not created
**Solution**:
```bash
# Recreate vault structure
python scripts/setup.sh

# Or manually:
mkdir -p vault/{Inbox,Plans,Needs_Action,Pending_Approval,Approved,Rejected,Done,Logs}
```

#### Issue: Orchestrator not processing inbox items
**Cause**: Watchdog not triggering or Claude not responding
**Solution**:
```bash
# Check orchestrator running
ps aux | grep orchestrator

# Restart orchestrator
killall python3
python scripts/orchestrator.py &

# Check file creation timestamp
ls -la vault/Inbox/ | head -1

# Verify Claude is accessible
curl https://api.anthropic.com/ping
```

#### Issue: "Plan creation failed: No response"
**Cause**: Claude API timeout or token limit
**Solution**:
1. Check Claude API key: `echo $ANTHROPIC_API_KEY`
2. Check API status: https://status.anthropic.com/
3. Reduce vault size (archive old items)
4. Increase timeout: `CLAUDE_TIMEOUT=120`

---

### MCP Server Issues

#### Issue: "MCP Email server connection failed"
**Cause**: MCP server not running or wrong configuration
**Solution**:
```bash
# Start MCP servers manually
node mcp_servers/email_mcp/index.js

# Check configuration
cat mcp_config.json

# Verify Node.js installed
node --version  # Should be 24+

# Update dependencies
cd mcp_servers/email_mcp && npm install
```

#### Issue: "Xero MCP: Invalid account format"
**Cause**: Wrong Xero organization selected
**Solution**:
1. Log into Xero dashboard
2. Switch to correct organization (top-left)
3. Copy Xero Tenant ID from settings
4. Update `.env`: `XERO_TENANT_ID=xxxx-xxxx-xxxx`

#### Issue: "Social Media MCP: Token expired"
**Cause**: Access token older than 60 days
**Solution**:
1. Re-authenticate on Meta Business Dashboard
2. Generate new Access Token
3. Update `.env`: `META_ACCESS_TOKEN=new_token`
4. Restart MCP server

---

### File System Issues

#### Issue: "vault/Logs directory full"
**Cause**: Log files not being archived
**Solution**:
```bash
# Check log size
du -sh vault/Logs

# Archive old logs (older than 30 days)
find vault/Logs -name "*.json" -mtime +30 -exec gzip {} \;

# Or clean completely
rm -f vault/Logs/*.json

# Configure log rotation
# Edit vault/Logs/audit_rules.md for retention policy
```

#### Issue: "vault/Pending_Approval grows infinitely"
**Cause**: Approved items not being executed
**Solution**:
```bash
# Check for stuck approvals
ls -la vault/Pending_Approval | head -5

# Manually move approved items
mv vault/Pending_Approval/approved_item.md vault/Approved/

# Check orchestrator processing
tail -100 vault/Logs/*.json | grep "execution_error"

# Restart orchestrator
python scripts/orchestrator.py
```

#### Issue: "Permissions denied on vault directory"
**Cause**: Wrong user owns directory
**Solution**:
```bash
# Fix ownership
sudo chown -R $(whoami) vault/

# Fix permissions
chmod -R 755 vault/
chmod -R 644 vault/**/*.md

# Verify
ls -la vault/ | head -1
```

---

### Testing Issues

#### Issue: "pytest: command not found"
**Cause**: pytest not installed
**Solution**:
```bash
# Install pytest
pip install pytest pytest-cov

# Run tests with verbose output
python3 -m pytest tests/ -v
```

#### Issue: "Test fixtures not found"
**Cause**: Tests directory structure wrong
**Solution**:
```bash
# Create __init__.py files
touch tests/__init__.py
touch tests/fixtures.py

# Verify structure
ls -la tests/
# Should show: __init__.py, fixtures.py, test_*.py
```

#### Issue: "Integration tests timeout"
**Cause**: Vault operations slow on large datasets
**Solution**:
```bash
# Run with longer timeout
pytest tests/ --timeout=300

# Run specific test only
pytest tests/test_integration.py::TestEmailWatcherIntegration -v

# Skip slow tests
pytest tests/ -m "not slow"
```

---

### Performance Issues

#### Issue: Orchestrator running slowly (>5sec per action)
**Cause**: Large vault, network latency, or Claude rate limits
**Solution**:
1. Archive done items: `mv vault/Done/* vault/.archive/`
2. Reduce vault size (< 100 files)
3. Check network: `ping api.anthropic.com`
4. Increase check interval: `ORCHESTRATOR_INTERVAL=300`

#### Issue: "Gmail watcher taking 30+ seconds"
**Cause**: Gmail API slow or network issue
**Solution**:
```bash
# Check Gmail API response time
time curl https://www.googleapis.com/gmail/v1/users/me/profile

# Reduce check frequency
echo "GMAIL_CHECK_INTERVAL=600" >> .env

# Check connection quality
ping -c 5 gmail.google.com
```

#### Issue: Memory usage increasing over time
**Cause**: Watcher not cleaning up connections
**Solution**:
```bash
# Monitor memory
top -o %MEM

# Restart watcher daily
# Add to crontab: 0 0 * * * pkill -f gmail_watcher
crontab -e

# Or use watchdog script
python scripts/watchdog.py
```

---

### Error Recovery

#### Issue: "Action failed - retry exceeded"
**Cause**: External service unavailable
**Solution**:
```bash
# Check retry log
grep "retry_exceeded" vault/Logs/*.json

# Manually move to rejected
mv vault/Approved/action.md vault/Rejected/action.md

# Add note about failure
echo "\n## Failed at $(date)\nReason: External service unavailable" >> vault/Rejected/action.md

# Investigate error
tail -20 vault/Logs/2026-01-08.json | jq '.[] | select(.result=="failed")'
```

#### Issue: "Audit log corrupted - can't parse JSON"
**Cause**: Partial write or encoding issue
**Solution**:
```bash
# Validate JSON syntax
python3 -m json.tool vault/Logs/2026-01-08.json

# Extract valid entries only
grep -v "^$" vault/Logs/2026-01-08.json > vault/Logs/2026-01-08.valid.json

# Backup corrupted log
mv vault/Logs/2026-01-08.json vault/Logs/2026-01-08.corrupted.json
mv vault/Logs/2026-01-08.valid.json vault/Logs/2026-01-08.json
```

---

## Getting Help

### Debug Mode
```bash
# Run any component with debug logging
python watchers/gmail_watcher.py --debug --log-level DEBUG

# Check logs in real-time
tail -f vault/Logs/*.json

# Monitor system resources
watch -n 1 'ps aux | grep python'
```

### Health Check
```bash
# Run verification script
python Setup_Verify.py

# Test all components
python scripts/test_all.py

# Check component status
echo "Orchestrator: $(pgrep -f orchestrator.py > /dev/null && echo 'running' || echo 'stopped')"
echo "Gmail watcher: $(pgrep -f gmail_watcher > /dev/null && echo 'running' || echo 'stopped')"
echo "WhatsApp watcher: $(pgrep -f whatsapp_watcher > /dev/null && echo 'running' || echo 'stopped')"
```

### Log Analysis
```bash
# Find errors
grep -i "error\|failed\|exception" vault/Logs/*.json

# Count by action type
jq -r '.action_type' vault/Logs/*.json | sort | uniq -c

# Recent activity
tail -20 vault/Logs/*.json | jq '.'
```

---

## FAQ

**Q: How often do watchers check for updates?**
A: Default is 120 seconds. Adjust with `*_CHECK_INTERVAL` in `.env`

**Q: Can I use free tier APIs?**
A: Yes, but with limits. Gmail (free), WhatsApp (requires business account), Xero (14-day free trial), Twitter (elevated access required)

**Q: Does vault auto-backup?**
A: No. Backup manually: `cp -r vault vault.backup`

**Q: Can multiple users use same vault?**
A: Not recommended (file conflicts). Use separate vaults per user.

**Q: How long are logs kept?**
A: Default 90 days. Configure in `vault/Logs/audit_rules.md`

---

See `ARCHITECTURE.md` for system design details or `LESSONS_LEARNED.md` for troubleshooting patterns from development.
