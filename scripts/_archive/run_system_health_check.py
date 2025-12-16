"""
System Health Check CLI
Runs the system health check, saves the report, and logs alerts.
Usage: python scripts/run_system_health_check.py
"""

import sys
from pathlib import Path
import logging

# Add project root parent to path to allow 'garam' package import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.monitoring.health_check import run_system_health_check
from garam.monitoring.health_report import save_health_report
from garam.monitoring.alerting import log_alert

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("HealthCLI")

def main():
    logger.info("Running System Health Check...")
    
    try:
        # 1. Run Check
        health = run_system_health_check()
        
        # 2. Save Report
        save_health_report(health)
        
        # 3. Log Alerts
        log_alert(health)
        
        # 4. Print Summary
        status = health['status']
        icon = "OK" if status == "OK" else "WARN" if status == "WARN" else "ERROR"
        logger.info(f"Health Check Complete: [{icon}] {status}")
        
        if status != "OK":
            logger.info("Issues found. Check logs/alerts.log or health report for details.")
            sys.exit(1) # Exit with error code for scheduler
            
    except Exception as e:
        logger.error(f"Health Check Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
