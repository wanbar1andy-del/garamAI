"""
Alerting Module
Logs alerts to a dedicated file based on system health status.
"""

import logging
from pathlib import Path
from typing import Dict

# Try importing from garam.config if available
try:
    from garam.config import PATHS
except ImportError:
    try:
        from config import PATHS
    except ImportError:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PATHS

def log_alert(health: Dict):
    """
    Log alerts if status is WARN or ERROR.
    """
    status = health.get("status", "UNKNOWN")
    
    if status == "OK":
        return
        
    # Setup alert logger
    alert_log_path = PATHS.LOGS_DIR / "alerts.log"
    
    # Create a dedicated logger for alerts to avoid messing with root logger
    alert_logger = logging.getLogger("SystemAlerts")
    alert_logger.setLevel(logging.WARNING)
    
    # Check if handler already exists to avoid duplicates
    if not alert_logger.handlers:
        handler = logging.FileHandler(alert_log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        alert_logger.addHandler(handler)
        
    msg = f"System Status: {status} | Mode: {health['mode']['trading_mode']}"
    
    # Add details
    if health['mode']['status'] != 'OK':
        msg += f" | Mode Error: {health['mode']['message']}"
        
    if health['data']['status'] != 'OK':
        msg += " | Data Issues Detected"
        
    if health['shadow']['status'] != 'OK':
        msg += f" | Shadow Issue: {health['shadow']['message']}"
        
    if status == "ERROR":
        alert_logger.error(msg)
    else:
        alert_logger.warning(msg)
