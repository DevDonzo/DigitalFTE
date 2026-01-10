# Error Recovery Agent Skill

**Skill ID**: `error-recovery`
**Type**: System Resilience / Watchdog
**Tier**: Gold
**Dependencies**: Process monitor, audit logs

## Purpose

Ensure system reliability through automatic process monitoring, failure detection, and graceful recovery with exponential backoff.

## Architecture

```
Process Monitor (Watchdog)
    |
Checks every 60 seconds:
  |-- Orchestrator running?
  |-- Gmail Watcher running?
  +-- Other critical processes
    |
If process down:
  |-- Log failure to audit trail
  |-- Calculate backoff delay
  |-- Attempt restart
  +-- Track retry count
    |
If max retries exceeded:
  |-- Alert for manual intervention
  +-- Stop automatic restarts
```

## Implementation

### Process Monitor
- **File**: `scripts/process_monitor.py`
- **Function**: `check_and_restart()`
- **Interval**: 60 seconds

### Error Recovery Settings
```python
MAX_RETRIES = 5
INITIAL_BACKOFF = 5  # seconds
MAX_BACKOFF = 300    # 5 minutes (exponential growth)
```

## Capabilities

### Process Monitoring
- Track PID files for each critical process
- Detect crashed or stopped processes
- Monitor process health continuously

### Exponential Backoff
- Initial delay: 5 seconds
- Doubles with each failure: 5 -> 10 -> 20 -> 40 -> 80 -> 160 -> 300 (capped)
- Prevents rapid restart loops

### Failure Logging
- Logs all failures to `vault/Logs/process_failures.jsonl`
- Records timestamp, process name, retry count
- Enables post-incident analysis

### Graceful Degradation
- Individual process failures don't crash entire system
- Other processes continue running
- Automatic recovery when possible

## Monitored Processes

| Process | Command | Purpose |
|---------|---------|---------|
| orchestrator | `python3 scripts/orchestrator.py` | Core workflow engine |
| gmail_watcher | `python3 watchers/gmail_watcher.py` | Email monitoring |

## Usage

### Start Watchdog
```bash
cd /Users/hparacha/DigitalFTE
python3 scripts/process_monitor.py
```

### Check Status
```bash
# View PID files
ls -la ~/.digitalfte_pids/

# View failure log
cat vault/Logs/process_failures.jsonl | jq '.'
```

## Failure Log Format

```json
{
  "timestamp": "2026-01-10T11:00:00Z",
  "process": "orchestrator",
  "retries": 2,
  "error": null,
  "action": "restart_attempted"
}
```

## Recovery Flow

1. **Detection**: Process PID file exists but process not running
2. **Check Retries**: Under MAX_RETRIES?
3. **Calculate Backoff**: 5 * 2^retries (capped at 300)
4. **Wait**: If within backoff window, skip restart
5. **Log**: Record failure to audit trail
6. **Restart**: Start process, save new PID
7. **Reset**: On successful run, reset retry count

## Safety Features

- **Max Retries**: Stops after 5 failed attempts
- **Backoff Cap**: Never waits more than 5 minutes
- **PID Tracking**: Prevents duplicate processes
- **Audit Trail**: All failures logged for analysis

## Manual Intervention Required

When max retries exceeded:
1. Check logs: `cat vault/Logs/process_failures.jsonl | tail -20`
2. Identify root cause
3. Fix underlying issue
4. Restart watchdog: `python3 scripts/process_monitor.py`

## Status

IMPLEMENTED
- Process monitoring
- Exponential backoff
- Failure logging
- Graceful degradation
- Max retry limits
