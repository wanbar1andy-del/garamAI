import threading
import time
import json
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    import psutil
except ImportError:
    psutil = None

from garam.config import PATHS

logger = logging.getLogger(__name__)

class HealthCollector:
    """
    Background service to collect system health metrics and save to JSON.
    """
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.last_check = None
        
        # Ensure directory exists
        self.health_dir = PATHS.HEALTH_DIR
        self.health_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the collector in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"HealthCollector started (Interval: {self.interval}s)")

    def stop(self):
        """Stop the collector."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("HealthCollector stopped")

    def _run_loop(self):
        """Main loop."""
        while self.running:
            try:
                self.collect_and_save()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            
            # Sleep in chunks to allow faster stopping
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def collect_and_save(self):
        """Collect metrics and save to JSON."""
        metrics = self._gather_metrics()
        self._save_to_file(metrics)
        self.last_check = datetime.now()

    def _gather_metrics(self) -> Dict[str, Any]:
        """Gather all system metrics."""
        now = datetime.now()
        
        # 1. Kiwoom Status
        kiwoom_flag = PATHS.KIWOOM_FLAG_PATH
        kiwoom_connected = kiwoom_flag.exists()
        
        # 2. System Resources (CPU/Mem)
        cpu_pct = 0.0
        mem_pct = 0.0
        if psutil:
            try:
                cpu_pct = psutil.cpu_percent(interval=None)
                mem_pct = psutil.virtual_memory().percent
            except:
                pass
        
        # 3. Disk Space (GARAM_Data drive)
        disk_info = {"free_gb": 0, "percent": 0}
        try:
            total, used, free = shutil.disk_usage(str(PATHS.DATA_DIR))
            disk_info = {
                "free_gb": round(free / (1024**3), 2),
                "percent": round((used / total) * 100, 1)
            }
        except:
            pass

        # 4. Mode Config
        mode = "UNKNOWN"
        try:
            from garam.config import load_trading_mode
            mode_cfg = load_trading_mode()
            mode = mode_cfg.get('trading_mode', 'UNKNOWN')
        except:
            pass

        # Overall Status Logic
        status = "OK"
        if not kiwoom_connected:
            status = "WARNING" # Kiwoom disconnected
        if disk_info['percent'] > 90:
            status = "WARNING" # Disk full
        
        return {
            "timestamp": now.isoformat(),
            "status": status,
            "components": {
                "kiwoom": {
                    "status": "CONNECTED" if kiwoom_connected else "DISCONNECTED",
                    "flag_path": str(kiwoom_flag)
                },
                "server": {
                    "status": "RUNNING",
                    "pid": os.getpid()
                },
                "disk": disk_info
            },
            "resources": {
                "cpu_percent": cpu_pct,
                "memory_percent": mem_pct
            },
            "mode": {
                "trading_mode": mode
            }
        }

    def _save_to_file(self, metrics: Dict[str, Any]):
        """Save metrics to daily JSON file."""
        filename = f"health_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.health_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            logger.debug(f"Health metrics saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save health metrics: {e}")

# Singleton instance
_health_collector = None

def get_health_collector():
    global _health_collector
    if _health_collector is None:
        _health_collector = HealthCollector()
    return _health_collector
