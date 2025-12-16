"""
Alert Manager for GARAM Trading System
Handles error classification and alert routing
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

# Import centralized paths
try:
    from garam.config import PATHS
    DEFAULT_LOG_DIR = str(PATHS.LOGS_DIR)
except ImportError:
    DEFAULT_LOG_DIR = "C:/garam/GARAM_Data/logs"


class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"  # RED
    WARNING = "WARNING"    # ORANGE
    INFO = "INFO"          # GREEN


class Alert:
    """Individual alert object"""
    def __init__(
        self,
        level: AlertLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        alert_id: Optional[str] = None
    ):
        self.level = level
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now()
        self.alert_id = alert_id or f"{level.value}_{int(self.timestamp.timestamp())}"
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }


class AlertHandler:
    """Base class for alert handlers"""
    def handle(self, alert: Alert):
        raise NotImplementedError


class ConsoleHandler(AlertHandler):
    """Print alerts to console"""
    def __init__(self):
        self.logger = logging.getLogger('garam.alerts.console')
    
    def handle(self, alert: Alert):
        level_emoji = {
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.WARNING: "🟠",
            AlertLevel.INFO: "🟢"
        }
        emoji = level_emoji.get(alert.level, "⚪")
        self.logger.warning(f"{emoji} [{alert.level.value}] {alert.message}")


class FileHandler(AlertHandler):
    """Write alerts to log file"""
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir) if log_dir else Path(DEFAULT_LOG_DIR)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('garam.alerts.file')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        log_file = self.log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    def handle(self, alert: Alert):
        self.logger.log(
            logging.CRITICAL if alert.level == AlertLevel.CRITICAL else logging.WARNING,
            json.dumps(alert.to_dict(), ensure_ascii=False)
        )


class DashboardHandler(AlertHandler):
    """Store alerts for dashboard display"""
    def __init__(self):
        self.alerts: List[Alert] = []
        self.max_alerts = 100  # Keep last 100 alerts
    
    def handle(self, alert: Alert):
        self.alerts.append(alert)
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
    
    def get_active_alerts(self, acknowledged: bool = False) -> List[Dict[str, Any]]:
        """Get alerts that haven't been acknowledged"""
        return [
            a.to_dict() for a in self.alerts
            if a.acknowledged == acknowledged
        ]
    
    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break


class AlertManager:
    """
    Central alert management system
    Routes alerts to appropriate handlers based on severity
    """
    
    def __init__(self):
        # Initialize handlers
        self.console_handler = ConsoleHandler()
        self.file_handler = FileHandler()
        self.dashboard_handler = DashboardHandler()
        
        # Define routing rules
        self.channels = {
            AlertLevel.CRITICAL: [
                self.console_handler,
                self.file_handler,
                self.dashboard_handler
            ],
            AlertLevel.WARNING: [
                self.file_handler,
                self.dashboard_handler
            ],
            AlertLevel.INFO: [
                self.file_handler
            ]
        }
        
        self.logger = logging.getLogger('garam.alert_manager')
    
    def emit_alert(
        self,
        level: AlertLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Emit an alert to appropriate channels
        
        Args:
            level: Alert severity
            message: Alert message
            context: Additional context
            
        Returns:
            Created alert object
        """
        alert = Alert(level, message, context)
        
        # Route to handlers
        handlers = self.channels.get(level, [])
        for handler in handlers:
            try:
                handler.handle(alert)
            except Exception as e:
                self.logger.error(f"Handler failed: {e}")
        
        return alert
    
    def emit_critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Emit CRITICAL alert"""
        return self.emit_alert(AlertLevel.CRITICAL, message, context)
    
    def emit_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Emit WARNING alert"""
        return self.emit_alert(AlertLevel.WARNING, message, context)
    
    def emit_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Emit INFO alert"""
        return self.emit_alert(AlertLevel.INFO, message, context)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system health status
        
        Returns:
            status: GREEN/ORANGE/RED
            active_alerts: List of unacknowledged alerts
            alert_counts: Count by severity
        """
        active_alerts = self.dashboard_handler.get_active_alerts(acknowledged=False)
        
        # Determine overall status
        has_critical = any(a['level'] == 'CRITICAL' for a in active_alerts)
        has_warning = any(a['level'] == 'WARNING' for a in active_alerts)
        
        if has_critical:
            status = "RED"
        elif has_warning:
            status = "ORANGE"
        else:
            status = "GREEN"
        
        # Count alerts by level
        counts = {
            'CRITICAL': sum(1 for a in active_alerts if a['level'] == 'CRITICAL'),
            'WARNING': sum(1 for a in active_alerts if a['level'] == 'WARNING'),
            'INFO': sum(1 for a in active_alerts if a['level'] == 'INFO')
        }
        
        return {
            'status': status,
            'active_alerts': active_alerts,
            'alert_counts': counts,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_dashboard_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts for dashboard display"""
        return self.dashboard_handler.get_active_alerts(acknowledged=False)
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        self.dashboard_handler.acknowledge_alert(alert_id)


# Singleton instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get or create singleton alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


if __name__ == "__main__":
    # Test the alert manager
    manager = AlertManager()
    
    # Test different alert levels
    manager.emit_critical("API Connection Lost", {'api': 'Kiwoom', 'retry': 3})
    manager.emit_warning("High slippage detected", {'slippage': 0.8, 'threshold': 0.5})
    manager.emit_info("Daily trading session started")
    
    # Check system status
    status = manager.get_system_status()
    print(f"System Status: {status['status']}")
    print(f"Active Alerts: {len(status['active_alerts'])}")
    print(f"Alert Counts: {status['alert_counts']}")
