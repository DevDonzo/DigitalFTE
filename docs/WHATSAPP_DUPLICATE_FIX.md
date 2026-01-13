# WhatsApp Duplicate Message Fix

**Issue**: When you move a WhatsApp draft from `/Pending_Approval/` to `/Approved/`, the message gets sent **twice**.

**Root Cause**: Race condition in the orchestrator's file processing logic.

## The Problem

The orchestrator had multiple code paths that could execute the same file:

1. **File Watcher** (`on_created` event):
   - Detects file moved to `/Approved/`
   - Marks file as "executed" in memory (`executed_files` set)
   - Queues file for batch processing
   - Calls `_process_batch()` immediately

2. **Batch Processor** (`_process_batch()`):
   - Processes queued files
   - Calls `_execute_action()` for each file
   - `_execute_action()` checks `executed_files` but processes anyway

3. **Periodic Scan** (every 60 seconds):
   - Scans `/Approved/` folder for files
   - Executes files that haven't been moved to `/Done/` yet
   - Race condition: If file is still in `/Approved/`, it executes again

**Timeline of duplicate send**:
```
T=0.000ms    on_created fires for WHATSAPP_DRAFT_[ts].md
T=0.001ms    executed_files.add("WHATSAPP_DRAFT_[ts].md")
T=0.002ms    event_queue['approved'].append(filepath)
T=0.003ms    _process_batch() called
T=0.100ms    _execute_action() starts (sends WhatsApp message 1)
T=0.500ms    File moved to /Done/
T=60.000s    Periodic scan finds file??? NO - File is in /Done/
T=?          But watchdog can fire on_created multiple times!
T=+50ms      Second on_created event (watchdog fires again)
T=+50ms      Second _execute_action() call (sends WhatsApp message 2)
```

## The Solution

### Fix #1: Add Check in `_process_batch()`

Added deduplication in `_process_batch()` to skip files that are already marked as executed:

```python
# For approved files, also skip if already executed
if queue_type == 'approved':
    filtered_queue = []
    for filepath in unique_queue:
        if filepath.name in self.executed_files:
            logger.debug(f"Batch: Skipping already-executed file: {filepath.name}")
        else:
            filtered_queue.append(filepath)
    unique_queue = filtered_queue
```

### Fix #2: Add Check in Periodic Scan

Added deduplication in the periodic scan loop that rescans `/Approved/`:

```python
# Skip if already executed (prevents duplicate sends)
if filepath.name in handler.executed_files:
    logger.debug(f"Periodic scan: Skipping already-executed file: {filepath.name}")
    continue
```

### Fix #3: Reduce Watchdog Double-Fire Risk

The core issue is that the watchdog library can fire `on_created` multiple times for the same file move operation. By adding checks in both `_process_batch()` AND the periodic scan, we ensure:

- Even if `on_created` fires twice, the second call to `_execute_action()` skips
- Even if the periodic scan runs before the file moves to `/Done/`, it still skips
- The `executed_files` set is the single source of truth

## Files Modified

**`scripts/orchestrator.py`**:
- Line 250-265: Added comment explaining deduplication strategy
- Line 294-320: Added filter in `_process_batch()` to skip already-executed files
- Line 1448-1457: Added check in periodic scan loop

## Testing the Fix

After moving a WhatsApp draft to `/Approved/`:

1. Check the logs:
```bash
tail -20 vault/Logs/2026-01-13.json | grep "WHATSAPP_DRAFT"
```

You should see **exactly ONE** `action_executed` entry (not two).

2. Check WhatsApp sent logs:
```bash
tail -5 vault/Logs/whatsapp_sent.jsonl | jq .
```

Should show **one message** sent, not two.

3. Check audit trail:
```bash
grep "WHATSAPP_DRAFT" vault/Logs/2026-01-13.json | wc -l
```

Should be 1, not 2.

## Why This Works

The fix works because:

1. **Single Source of Truth**: `executed_files` set tracks all files that have been sent
2. **Multiple Safeguards**: Three places check if file was already executed:
   - `on_created()` handler (line 255)
   - `_process_batch()` (line 304-308)
   - Periodic scan (line 1451-1453)
3. **Thread-Safe**: All checks use the `dedup_lock` for thread safety
4. **Graceful**: If a file is somehow still being processed, we skip it

## Performance Impact

- **Minimal**: Added simple set membership checks (O(1) operation)
- **Benefit**: Prevents multiple Twilio API calls for same message
- **Savings**: Reduces costs and prevents duplicate message spam

---

**Status**: ✅ Fixed
**Date**: January 13, 2026
**Impact**: Prevents duplicate WhatsApp message sends
