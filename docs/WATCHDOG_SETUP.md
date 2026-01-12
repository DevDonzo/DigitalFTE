# Watchdog Process Manager Setup

## Overview

The Watchdog monitors critical DigitalFTE processes and automatically restarts them if they crash. It provides:

- **Auto-restart** on process failure
- **Startup persistence** (starts on system boot)
- **Rate limiting** (prevents restart loops)
- **Logging** to `vault/Logs/watchdog.out`
- **Status tracking** in `vault/Logs/watchdog_status.json`

## Processes Monitored

1. **orchestrator** - Main coordination engine
2. **gmail_watcher** - Email monitoring
3. **whatsapp_watcher** - WhatsApp message handling
4. **linkedin_watcher** - LinkedIn monitoring
5. **webhook_server** - WhatsApp webhook receiver

## Setup Instructions (macOS)

### Option 1: Manual Start (Testing)

```bash
cd /path/to/DigitalFTE
python3 scripts/watchdog.py
```

### Option 2: Auto-Start on Boot (Production)

Install the macOS launch agent:

```bash
# Copy the plist file to Launch Agents
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/

# Load it (starts watchdog now + on every boot)
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist

# Verify it's loaded
launchctl list | grep digitalfte
```

### To Stop the Watchdog

```bash
launchctl unload ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
```

## Monitoring the Watchdog

### View Real-Time Log

```bash
tail -f vault/Logs/watchdog.out
```

### Check Process Status

```bash
# View JSON status file
cat vault/Logs/watchdog_status.json
```

### Verify Processes Are Running

```bash
ps aux | grep python | grep -E "(orchestrator|gmail_watcher|whatsapp_watcher|linkedin_watcher|webhook_server)"
```

## Configuration

Edit `scripts/watchdog.py` to adjust:

- **restart_delay**: Seconds to wait before restarting a crashed process
- **max_restarts**: Max restarts allowed within restart_window
- **restart_window**: Time window (seconds) for restart limits
- **check_interval**: How often watchdog checks process status

Default config:
- Checks every 30 seconds
- Logs status every 5 minutes
- Prevents restart loops (max 10 restarts per hour for orchestrator)

## How It Works

```
Watchdog Loop (every 30s):
  For each process:
    1. Check if PID file exists
    2. Check if process with that PID is running
    3. If not running:
       a. Check restart rate limit
       b. Wait restart_delay seconds
       c. Start new process
       d. Save new PID
       e. Log restart

Every 5 minutes:
  Write status JSON to vault/Logs/watchdog_status.json
```

## Troubleshooting

### "No such file or directory: 'python'"

**Solution**: Make sure watchdog uses `python3` (check scripts/watchdog.py)

### Process keeps restarting (restart loop)

**Cause**: Process is crashing immediately
**Solution**: Check `vault/Logs/[process_name].out` for error details

### Watchdog not starting on boot

**Check**:
```bash
launchctl list | grep digitalfte
```

**If not loaded**:
```bash
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
```

### Permission denied

**If plist has wrong owner**:
```bash
# Make sure file is readable
chmod 644 ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
```

## Testing the Watchdog

1. Start watchdog:
   ```bash
   python3 scripts/watchdog.py
   ```

2. Kill one of its processes:
   ```bash
   pkill -f "python3 scripts/orchestrator.py"
   ```

3. Watch logs:
   ```bash
   tail -f vault/Logs/watchdog.out
   ```

   You should see:
   ```
   orchestrator not running, restarting...
   🚀 Starting orchestrator...
   ✅ orchestrator started (PID: 12345)
   ```

## Alternative: Linux/systemd

If running on Linux, create `/etc/systemd/system/digitalfte-watchdog.service`:

```ini
[Unit]
Description=DigitalFTE Watchdog Process Manager
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/DigitalFTE
ExecStart=/usr/bin/python3 scripts/watchdog.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable digitalfte-watchdog
sudo systemctl start digitalfte-watchdog
```

## Logs

- **Main log**: `vault/Logs/watchdog.out`
- **Error log**: `vault/Logs/watchdog.err` (if using plist)
- **Status**: `vault/Logs/watchdog_status.json` (updated every 5 min)
- **Process logs**: `vault/Logs/[process].out` (individual process output)

---

**Status**: ✅ Ready for production use
