# otherwise fallback to local config (when running from root)
import logging
from datetime import datetime
from typing import Dict, Any
import json
from pathlib import Path
import shutil

try:
    from garam.config import PATHS
    from garam.data.loaders.kr_realtime_loader import KRRealtimeBarLoader
except ImportError:
    try:
        from config import PATHS
        from data.loaders.kr_realtime_loader import KRRealtimeBarLoader
    except ImportError:
        # Fallback for direct execution testing if path not set
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from config import PATHS
        from data.loaders.kr_realtime_loader import KRRealtimeBarLoader

logger = logging.getLogger(__name__)

def run_system_health_check() -> Dict[str, Any]:
    """
    Run all system health checks.
    Returns a dictionary with the health status.
    """
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "OK", # Will be downgraded to WARN or ERROR if issues found
        "mode": _check_trading_mode(),
        "data": _check_data_freshness(),
        "shadow": _check_shadow_report(),
        "metrics": _check_metrics(),
        "KR_REALTIME_FEED": _check_kr_realtime_feed(),
        "DISK_USAGE": _check_disk_usage()
    }
    
    # Aggregate status
    statuses = [
        health["mode"]["status"],
        health["data"]["status"],
        health["shadow"]["status"],
        health["metrics"]["status"],
        health["KR_REALTIME_FEED"]["status"],
        health["DISK_USAGE"]["status"]
    ]
    
    if "ERROR" in statuses:
        health["status"] = "ERROR"
    elif "WARN" in statuses:
        health["status"] = "WARN"
        
    return health

def _check_trading_mode() -> Dict[str, Any]:
    """Check if TRADING_MODE is SHADOW."""
    result = {"status": "OK", "trading_mode": "UNKNOWN", "message": ""}
    
    try:
        if PATHS.TRADING_MODE_FILE.exists():
            with open(PATHS.TRADING_MODE_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                mode = config.get('trading_mode', 'UNKNOWN')
                result["trading_mode"] = mode
                
                if mode != "SHADOW":
                    result["status"] = "ERROR"
                    result["message"] = f"Invalid Trading Mode: {mode}. Expected SHADOW."
                else:
                    result["message"] = "System is in SHADOW mode."
        else:
            result["status"] = "ERROR"
            result["message"] = "Trading mode config file missing."
            
    except Exception as e:
        result["status"] = "ERROR"
        result["message"] = f"Failed to check trading mode: {str(e)}"
        
    return result

def _check_data_freshness() -> Dict[str, Any]:
    """Check freshness of key data files."""
    result = {
        "status": "OK",
        "us_daily": {"status": "UNKNOWN", "latest": "N/A"},
        "kr_intraday": {"status": "UNKNOWN", "latest": "N/A"},
        "us_factors": {"status": "UNKNOWN", "latest": "N/A"}
    }
    
    # 1. US Daily Data (Mock check for now as we use mock/lake)
    # Check if US_SP500_ROOT has recent files
    try:
        # In a real scenario, we'd check the latest CSV date.
        # For now, check if directory exists and has files.
        if PATHS.US_SP500_ROOT.exists():
            files = list(PATHS.US_SP500_ROOT.glob("*.csv"))
            if files:
                result["us_daily"]["status"] = "OK"
                result["us_daily"]["latest"] = "Available" # Placeholder
            else:
                result["us_daily"]["status"] = "WARN"
                result["us_daily"]["latest"] = "Empty"
    except Exception:
        result["us_daily"]["status"] = "ERROR"

    # 2. KR Intraday (Check 005930 1m data)
    try:
        kr_file = PATHS.KR_ROOT / "intraday" / "1m" / "005930.csv"
        if kr_file.exists():
            # Check modification time
            mtime = datetime.fromtimestamp(kr_file.stat().st_mtime)
            result["kr_intraday"]["latest"] = mtime.strftime("%Y-%m-%d %H:%M")
            
            # If older than 2 days (weekend buffer), WARN
            if (datetime.now() - mtime).days > 2:
                result["kr_intraday"]["status"] = "WARN"
            else:
                result["kr_intraday"]["status"] = "OK"
        else:
            result["kr_intraday"]["status"] = "WARN" # Might not be loaded yet
            result["kr_intraday"]["latest"] = "Missing"
    except Exception:
        result["kr_intraday"]["status"] = "ERROR"

    # 3. US Factors (Check experiments output)
    try:
        # Find latest experiment
        exp_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
        if exp_dir.exists():
            exps = sorted(exp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if exps:
                latest_exp = exps[0]
                mtime = datetime.fromtimestamp(latest_exp.stat().st_mtime)
                result["us_factors"]["latest"] = mtime.strftime("%Y-%m-%d")
                result["us_factors"]["status"] = "OK"
            else:
                result["us_factors"]["status"] = "WARN"
    except Exception:
        result["us_factors"]["status"] = "ERROR"
        
    # Aggregate Data Status
    if any(result[k]["status"] == "ERROR" for k in ["us_daily", "kr_intraday", "us_factors"]):
        result["status"] = "ERROR"
    elif any(result[k]["status"] == "WARN" for k in ["us_daily", "kr_intraday", "us_factors"]):
        result["status"] = "WARN"
        
    return result

def _check_shadow_report() -> Dict[str, Any]:
    """Check if today's shadow report exists."""
    result = {"status": "OK", "latest_report": "None", "message": ""}
    
    today_str = datetime.now().strftime("%Y%m%d")
    report_file = PATHS.SHADOW_LOGS / f"shadow_report_{today_str}.md"
    
    if report_file.exists():
        result["latest_report"] = report_file.name
        result["message"] = "Today's report available."
    else:
        # Check if it's market hours? For now, just WARN if missing
        # But if it's morning, it might not exist yet.
        # Let's check for *any* recent report.
        result["status"] = "WARN"
        result["message"] = "Today's report not found."
        
        # Find latest
        try:
            reports = sorted(PATHS.SHADOW_LOGS.glob("shadow_report_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if reports:
                result["latest_report"] = reports[0].name
                result["message"] += f" Latest: {reports[0].name}"
        except Exception:
            pass
            
    return result

def _check_metrics() -> Dict[str, Any]:
    """Check portfolio metrics sanity."""
    result = {"status": "OK", "note": "", "details": {}}
    
    # Check for portfolio summary from simulation/shadow loop
    # Assuming it's saved in experiments/portfolio or logs/shadow
    # For now, let's look for a recent portfolio summary in logs/shadow (if shadow mode)
    # or experiments/portfolio (if backtest)
    
    # In Shadow Mode, we expect a summary in the daily report or a separate JSON
    # Let's check for a 'portfolio_status.json' if it existed, but for now
    # we'll check if we can find any recent portfolio state file.
    
    # As per prompt requirement: "If data missing, status=WARN"
    # We don't have a standardized portfolio state file defined in NP-4 yet besides the MD report.
    # So we will mark as WARN for now to be safe, or check if the shadow report exists (which we already do).
    
    # Let's try to find a portfolio summary JSON if we decided to save one in NP-4 (we didn't explicitly).
    # So we will return WARN as "No dedicated portfolio metrics file found".
    
    result["status"] = "WARN"
    result["note"] = "No dedicated portfolio metrics file found (NP-4 generated MD only)"
    
    return result

def _check_kr_realtime_feed() -> Dict[str, Any]:
    """Check KR Realtime Feed latency."""
    result = {
        "status": "OK", 
        "latency_sec": -1, 
        "details": "Initializing"
    }
    
    # Only check during market hours (09:00 - 15:30)
    now = datetime.now()
    market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if not (market_start <= now <= market_end):
        result["status"] = "OK"
        result["details"] = "Market Closed"
        return result
        
    try:
        # Load universe to check
        import yaml
        config_path = PATHS.CONFIG_DIR / "kr_shadow_universe.yaml"
        universe = []
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                conf = yaml.safe_load(f)
                universe = conf.get('universe', [])
        
        if not universe:
            result["status"] = "WARN"
            result["details"] = "Universe empty"
            return result
            
        loader = KRRealtimeBarLoader(PATHS.DATA_DIR / "kr" / "realtime", universe)
        latency = loader.get_data_latency()
        
        result["latency_sec"] = latency
        
        if latency == 9999:
            result["status"] = "ERROR"
            result["details"] = "No data found"
        elif latency > 120:
            result["status"] = "ERROR"
            result["details"] = f"Latency high: {latency}s"
        elif latency > 60:
            result["status"] = "WARN"
            result["details"] = f"Latency elevated: {latency}s"
        else:
            result["status"] = "OK"
            result["details"] = f"Latency: {latency}s"
            
    except Exception as e:
        result["status"] = "ERROR"
        result["details"] = f"Check failed: {str(e)}"
        
    return result

def _check_disk_usage() -> Dict[str, Any]:
    """Check disk usage of the data directory"""
    result = {"status": "OK", "used_percent": -1, "message": ""}
    try:
        # Get disk usage of the drive containing GARAM_Data
        total, used, free = shutil.disk_usage(str(PATHS.BASE_DIR))
        used_percent = (used / total) * 100
        result["used_percent"] = round(used_percent, 2)
        
        if used_percent > 90:
            result["status"] = "WARN"
            result["message"] = f"Disk usage high: {used_percent:.2f}%"
        else:
            result["message"] = f"Disk usage: {used_percent:.2f}%"
        return result
    except Exception as e:
        result["status"] = "UNKNOWN"
        result["message"] = f"Failed to check disk usage: {str(e)}"
        return result
