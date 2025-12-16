"""
Health Report Generator
Persists system health status to JSON and Markdown files.
"""

import json
import logging
from datetime import datetime
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

logger = logging.getLogger(__name__)

def save_health_report(health: Dict):
    """
    Save health report to logs/health/ directory.
    """
    health_dir = PATHS.LOGS_DIR / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d")
    
    # 1. Save JSON
    json_path = health_dir / f"health_report_{timestamp_str}.json"
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(health, f, indent=2, ensure_ascii=False)
        logger.info(f"Health JSON saved to {json_path}")
    except Exception as e:
        logger.error(f"Failed to save health JSON: {e}")
        
    # 2. Save Markdown
    md_path = health_dir / f"health_report_{timestamp_str}.md"
    try:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(_generate_markdown(health))
        logger.info(f"Health Markdown saved to {md_path}")
    except Exception as e:
        logger.error(f"Failed to save health Markdown: {e}")

def _generate_markdown(health: Dict) -> str:
    """Generate Markdown content from health dict."""
    md = f"# System Health Report ({health['timestamp'][:10]})\n\n"
    
    # Status Badge
    status = health['status']
    color = "🟢" if status == "OK" else "🟡" if status == "WARN" else "🔴"
    md += f"## Status: {color} {status}\n\n"
    
    # Mode
    md += "## Trading Mode\n"
    md += f"- Mode: **{health['mode']['trading_mode']}**\n"
    md += f"- Status: {health['mode']['status']}\n"
    md += f"- Message: {health['mode']['message']}\n\n"
    
    # Data Freshness
    md += "## Data Freshness\n"
    md += "| Component | Status | Latest |\n"
    md += "|---|---|---|\n"
    
    data = health['data']
    for key, info in data.items():
        if key == "status": continue
        md += f"| {key} | {info['status']} | {info['latest']} |\n"
    md += "\n"
    
    # Shadow
    md += "## Shadow Loop\n"
    md += f"- Status: {health['shadow']['status']}\n"
    md += f"- Latest Report: {health['shadow']['latest_report']}\n"
    md += f"- Message: {health['shadow']['message']}\n\n"
    
    return md
