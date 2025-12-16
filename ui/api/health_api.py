"""
System Health API
Exposes the latest system health report.
"""

import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify

# Try importing from garam.config if available
try:
    from garam.config import PATHS
except ImportError:
    try:
        from config import PATHS
    except ImportError:
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from config import PATHS

logger = logging.getLogger(__name__)

health_bp = Blueprint('health_bp', __name__)

@health_bp.route('/system/health/latest', methods=['GET'])
def get_latest_health():
    """Get the latest health report."""
    try:
        health_dir = PATHS.LOGS_DIR / "health"
        
        # Find latest JSON report
        if not health_dir.exists():
            return jsonify({"error": "Health logs directory not found"}), 404
            
        reports = sorted(health_dir.glob("health_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not reports:
            return jsonify({"error": "No health reports found"}), 404
            
        latest_report = reports[0]
        
        with open(latest_report, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching health report: {e}")
        return jsonify({"error": str(e)}), 500
