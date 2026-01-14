"""Process Watchdog - Monitors and restarts critical processes"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Setup logging
log_dir = Path(os.getenv('VAULT_PATH', './vault')) / 'Logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'watchdog.out'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Critical processes to monitor
PROCESSES = {
    'orchestrator': {
        'cmd': 'python3 agents/orchestrator.py',
        'pid_file': Path('/tmp/digitalfte_orchestrator.pid'),
        'restart_delay': 5,
        'max_restarts': 10,
        'restart_window': 3600  # 1 hour
    },
    'gmail_watcher': {
        'cmd': 'python3 agents/gmail_watcher.py',
        'pid_file': Path('/tmp/digitalfte_gmail_watcher.pid'),
        'restart_delay': 3,
        'max_restarts': 5,
        'restart_window': 3600
    },
    'whatsapp_watcher': {
        'cmd': 'python3 agents/whatsapp_watcher.py',
        'pid_file': Path('/tmp/digitalfte_whatsapp_watcher.pid'),
        'restart_delay': 3,
        'max_restarts': 5,
        'restart_window': 3600
    },
    'webhook_server': {
        'cmd': 'python3 agents/webhook_server.py',
        'pid_file': Path('/tmp/digitalfte_webhook.pid'),
        'restart_delay': 5,
        'max_restarts': 10,
        'restart_window': 3600
    }
}

# Track restarts per process
restart_history = {name: [] for name in PROCESSES}


def is_process_running(pid: int) -> bool:
    """Check if process with given PID is running"""
    try:
        os.kill(pid, 0)  # Signal 0 = check if alive
        return True
    except (OSError, ProcessLookupError):
        return False


def get_process_pid(name: str) -> int:
    """Get PID from file, return None if invalid/dead"""
    pid_file = PROCESSES[name]['pid_file']
    
    if not pid_file.exists():
        return None
    
    try:
        pid = int(pid_file.read_text().strip())
        if is_process_running(pid):
            return pid
        else:
            pid_file.unlink()  # Remove stale PID file
            return None
    except (ValueError, OSError):
        return None


def start_process(name: str) -> bool:
    """Start a process and save its PID"""
    config = PROCESSES[name]
    logger.info(f"🚀 Starting {name}...")
    
    try:
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        
        # Start process
        proc = subprocess.Popen(
            config['cmd'].split(),
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Save PID
        config['pid_file'].write_text(str(proc.pid))
        logger.info(f"✅ {name} started (PID: {proc.pid})")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to start {name}: {e}")
        return False


def restart_process(name: str) -> bool:
    """Restart a process with rate limiting"""
    config = PROCESSES[name]
    now = time.time()
    
    # Check restart history for rate limiting
    recent_restarts = [
        t for t in restart_history[name]
        if now - t < config['restart_window']
    ]
    
    if len(recent_restarts) >= config['max_restarts']:
        logger.error(
            f"⚠️  {name} exceeded max restarts ({config['max_restarts']}) "
            f"in {config['restart_window']}s window. Pausing."
        )
        return False
    
    # Kill old process if still running
    old_pid = get_process_pid(name)
    if old_pid:
        try:
            os.killpg(os.getpgid(old_pid), 9)
            logger.warning(f"🛑 Killed old {name} process (PID: {old_pid})")
        except:
            pass
    
    # Wait before restart
    time.sleep(config['restart_delay'])
    
    # Record restart and start
    restart_history[name].append(now)
    return start_process(name)


def check_and_restart_all():
    """Check all processes and restart if needed"""
    for name in PROCESSES:
        pid = get_process_pid(name)
        
        if pid is None:
            logger.warning(f"⏭️  {name} not running, restarting...")
            restart_process(name)
        else:
            logger.debug(f"✓ {name} is running (PID: {pid})")


def log_status():
    """Log current status of all processes"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'processes': {}
    }
    
    for name in PROCESSES:
        pid = get_process_pid(name)
        status['processes'][name] = {
            'running': pid is not None,
            'pid': pid,
            'restarts_in_window': len(restart_history[name])
        }
    
    status_file = (Path(os.getenv('VAULT_PATH', './vault')) / 'Logs' / 'watchdog_status.json')
    status_file.write_text(json.dumps(status, indent=2))
    
    return status


def main():
    """Main watchdog loop"""
    logger.info("=" * 60)
    logger.info("🐕 DigitalFTE Watchdog Started")
    logger.info("=" * 60)
    logger.info(f"Monitoring processes: {', '.join(PROCESSES.keys())}")
    
    # Start all processes on first run
    for name in PROCESSES:
        if get_process_pid(name) is None:
            start_process(name)
    
    # Main monitoring loop
    check_interval = 30  # Check every 30 seconds
    status_interval = 300  # Log status every 5 minutes
    last_status_time = time.time()
    
    try:
        while True:
            check_and_restart_all()
            
            # Log status periodically
            if time.time() - last_status_time > status_interval:
                status = log_status()
                running = sum(1 for p in status['processes'].values() if p['running'])
                logger.info(f"📊 Status: {running}/{len(PROCESSES)} processes running")
                last_status_time = time.time()
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        logger.info("🛑 Watchdog stopped by user")
    except Exception as e:
        logger.error(f"❌ Watchdog error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
