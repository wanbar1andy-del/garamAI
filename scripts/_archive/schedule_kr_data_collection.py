"""
Schedule KR Data Collection
Runs daily at 15:35 KST (Market Close + 5 mins)

With infinite loop prevention safeguards:
- Max iterations limit
- Max runtime limit
- Graceful SIGINT handling
"""

import time
import subprocess
import logging
import argparse
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from utils.safe_scheduler import SafeScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PATHS.LOGS_DIR / "scheduler.log")
    ]
)
logger = logging.getLogger(__name__)

def run_collection():
    """Run the collection script"""
    # Check if weekend (0=Mon, 6=Sun)
    weekday = datetime.now().weekday()
    if weekday >= 5:
        logger.info("Weekend - skipping collection")
        return

    logger.info("Starting scheduled data collection...")
    
    try:
        script_path = project_root / "scripts" / "collect_kr_intraday_kiwoom.py"
        
        # Run collection script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Collection completed successfully")
            logger.info(result.stdout)
        else:
            logger.error("Collection failed")
            logger.error(result.stderr)
            
    except subprocess.TimeoutExpired:
        logger.error("Collection script timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Schedule KR data collection")
    parser.add_argument('--max-iterations', type=int, help='Maximum iterations before stopping')
    parser.add_argument('--max-runtime-hours', type=float, default=24, help='Maximum runtime in hours (default: 24)')
    parser.add_argument('--run-now', action='store_true', help='Run collection immediately and exit')
    args = parser.parse_args()
    
    logger.info("KR Data Collection Scheduler Started")
    logger.info("Schedule: Daily at 15:35 KST")
    
    # Run once immediately if requested
    if args.run_now:
        run_collection()
        return
    
    # Create safe scheduler
    scheduler = SafeScheduler(
        max_iterations=args.max_iterations,
        max_runtime_hours=args.max_runtime_hours,
        name="KRDataCollectionScheduler"
    )
    
    logger.info("Waiting for next scheduled run...")
    logger.info(f"Safety limits: max_iter={args.max_iterations}, max_hours={args.max_runtime_hours}")
    
    while scheduler.should_continue():
        now = datetime.now()
        
        # Target time: 15:35
        if now.hour == 15 and now.minute == 35:
            run_collection()
            # Sleep for 61 seconds to avoid double execution
            time.sleep(61)
        else:
            # Check every 30 seconds
            time.sleep(30)
        
        scheduler.tick()
    
    # Log final stats
    stats = scheduler.get_stats()
    logger.info(f"Scheduler stopped: {stats}")

if __name__ == "__main__":
    main()
