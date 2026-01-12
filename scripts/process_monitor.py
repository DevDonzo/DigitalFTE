"""Watchdog - Monitors and restarts critical processes with error recovery"""
import subprocess
import time
import logging
import os
import json
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VAULT_PATH = Path(os.getenv('VAULT_PATH', PROJECT_ROOT / 'vault'))

# Processes to monitor (name -> command)
PROCESSES = {
    'orchestrator': 'python3 scripts/orchestrator.py',
    'gmail_watcher': 'python3 watchers/gmail_watcher.py',
    'whatsapp_watcher': 'python3 watchers/whatsapp_watcher.py',
}

# Error recovery settings
MAX_RETRIES = 5
INITIAL_BACKOFF = 5  # seconds
MAX_BACKOFF = 300  # 5 minutes
retry_counts = {}
last_failure_time = {}

# Track process handles
running_processes = {}
pid_files = Path.home() / '.digitalfte_pids'
pid_files.mkdir(exist_ok=True)

def get_pid_file(process_name: str) -> Path:
    """Get PID file path for a process"""
    return pid_files / f'{process_name}.pid'

def is_process_running(process_name: str) -> bool:
    """Check if process is running by PID"""
    pid_file = get_pid_file(process_name)
    if not pid_file.exists():
        return False

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        # Check if process with this PID exists
        os.kill(pid, 0)  # Raises if process doesn't exist
        return True
    except (ValueError, OSError, ProcessLookupError):
        # Process doesn't exist or PID file is invalid
        return False

def start_process(name: str, cmd: str):
    """Start a process and save its PID"""
    try:
        logger.info(f'Starting {name}...')
        # Run in current directory
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )

        # Save PID
        pid_file = get_pid_file(name)
        pid_file.write_text(str(proc.pid))

        running_processes[name] = proc
        logger.info(f'✅ {name} started (PID: {proc.pid})')
        return proc
    except Exception as e:
        logger.error(f'Failed to start {name}: {e}')
        return None

def stop_process(name: str):
    """Stop a running process"""
    if name in running_processes:
        proc = running_processes[name]
        try:
            proc.terminate()
            proc.wait(timeout=5)
            logger.info(f'✋ {name} stopped')
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.warning(f'⚠️ {name} killed (timeout)')
        finally:
            del running_processes[name]

def calculate_backoff(name: str) -> int:
    """Calculate exponential backoff delay"""
    retries = retry_counts.get(name, 0)
    backoff = min(INITIAL_BACKOFF * (2 ** retries), MAX_BACKOFF)
    return backoff

def should_restart(name: str) -> bool:
    """Check if process should be restarted based on retry limits"""
    if retry_counts.get(name, 0) >= MAX_RETRIES:
        logger.error(f'❌ {name} exceeded max retries ({MAX_RETRIES}) - manual intervention required')
        return False
    return True

def log_failure(name: str, error: str = None):
    """Log process failure for audit trail"""
    vault_logs = VAULT_PATH / 'Logs'
    vault_logs.mkdir(parents=True, exist_ok=True)

    failure_log = {
        'timestamp': datetime.now().isoformat(),
        'process': name,
        'retries': retry_counts.get(name, 0),
        'error': error,
        'action': 'restart_attempted'
    }

    log_file = vault_logs / 'process_failures.jsonl'
    with open(log_file, 'a') as f:
        f.write(json.dumps(failure_log) + '\n')

def check_and_restart():
    """Check all processes and restart with exponential backoff"""
    for name, cmd in PROCESSES.items():
        if is_process_running(name):
            logger.debug(f'✅ {name} is running')
            # Reset retry count on successful run
            if name in retry_counts:
                retry_counts[name] = 0
        else:
            logger.warning(f'⚠️ {name} is not running')

            if not should_restart(name):
                continue

            # Calculate backoff
            backoff = calculate_backoff(name)
            last_fail = last_failure_time.get(name)

            if last_fail and (time.time() - last_fail) < backoff:
                logger.info(f'⏳ {name} waiting {backoff}s backoff (retry {retry_counts.get(name, 0)+1}/{MAX_RETRIES})')
                continue

            # Attempt restart
            log_failure(name)
            retry_counts[name] = retry_counts.get(name, 0) + 1
            last_failure_time[name] = time.time()

            logger.info(f'🔄 Restarting {name} (attempt {retry_counts[name]}/{MAX_RETRIES})')
            start_process(name, cmd)

def main():
    """Main watchdog loop"""
    logger.info('🐕 Watchdog started')

    # Start all processes
    for name, cmd in PROCESSES.items():
        if not is_process_running(name):
            start_process(name, cmd)

    try:
        while True:
            check_and_restart()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info('🛑 Stopping watchdog...')
        # Stop all processes
        for name in list(running_processes.keys()):
            stop_process(name)
        logger.info('✅ Watchdog stopped')

if __name__ == '__main__':
    main()
