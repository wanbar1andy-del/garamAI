"""
Shadow Loop Watchdog
Monitors the health of the Shadow Loop process.

With infinite loop prevention safeguards:
- Max iterations limit
- Max runtime limit
- Graceful SIGINT handling

Checks:
1. Process existence (via PID file or process name)
2. Log freshness (shadow_loop_YYYYMMDD.log updated in last N minutes)
"""

import time
import logging
import psutil
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS
from garam.monitoring.alerting import log_alert
from garam.utils.safe_scheduler import SafeScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ShadowWatchdog")

SHADOW_SCRIPT_NAME = "run_shadow_loop.py"
LOG_FRESHNESS_THRESHOLD_SEC = 300 # 5 minutes

def find_shadow_process():
    """Find the shadow loop process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and SHADOW_SCRIPT_NAME in ' '.join(cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def check_log_freshness():
    """Check if the latest shadow log file was updated recently"""
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = PATHS.SHADOW_LOGS / f"shadow_loop_{date_str}.log"
    
    if not log_file.exists():
        return False, "Log file not found"
        
    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
    age = (datetime.now() - mtime).total_seconds()
    
    if age > LOG_FRESHNESS_THRESHOLD_SEC:
        return False, f"Log stale (last update: {age:.0f}s ago)"
        
    return True, "Log fresh"

def run_watchdog(scheduler: SafeScheduler):
    logger.info("Starting Shadow Watchdog...")
    
    while scheduler.should_continue():
        # 1. Check Process
        proc = find_shadow_process()
        if not proc:
            msg = f"CRITICAL: {SHADOW_SCRIPT_NAME} is NOT running!"
            logger.error(msg)
            log_alert("SHADOW_DOWN", msg, level="ERROR")
        else:
            # 2. Check Log Freshness
            is_fresh, msg = check_log_freshness()
            if not is_fresh:
                logger.warning(f"Shadow Loop Stalled? {msg}")
                log_alert("SHADOW_STALLED", msg, level="WARN")
            else:
                logger.info(f"Shadow Loop OK (PID: {proc.pid})")
                
        time.sleep(60)
        scheduler.tick()
    
    # Log final stats
    stats = scheduler.get_stats()
    logger.info(f"Watchdog stopped: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Shadow Loop health")
    parser.add_argument('--max-iterations', type=int, help='Maximum iterations before stopping')
    parser.add_argument('--max-runtime-hours', type=float, default=24, help='Maximum runtime in hours (default: 24)')
    args = parser.parse_args()
    
    scheduler = SafeScheduler(
        max_iterations=args.max_iterations,
        max_runtime_hours=args.max_runtime_hours,
        name="ShadowWatchdog"
    )
    
    try:
        run_watchdog(scheduler)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user.")

