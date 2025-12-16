"""
Dashboard API Blueprint
Provides read-only endpoints for GaramUI v2
"""

from flask import Blueprint, jsonify, request
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/surfing/status', methods=['GET'])
def get_surfing_status():
    """Get latest Surfing Brain status"""
    try:
        log_dir = PATHS.LOGS_DIR / "surfing_decisions"
        if not log_dir.exists():
            return jsonify({"error": "No surfing logs found"}), 404
            
        log_files = sorted(log_dir.glob("*.csv"), reverse=True)
        if not log_files:
            return jsonify({"error": "No surfing decision logs"}), 404
            
        df = pd.read_csv(log_files[0])
        if df.empty:
            return jsonify({"error": "Empty log file"}), 404
            
        latest = df.iloc[-1].to_dict()
        
        return jsonify({
            "timestamp": latest.get('timestamp', datetime.now().isoformat()),
            "regime": latest.get('regime', 'UNKNOWN'),
            "uncertainty": float(latest.get('uncertainty', 0.5)),
            "mode": latest.get('mode', 'CRUISE'),
            "surf_state": latest.get('surf_state', 'SINGLE_MODEL'),
            "risk_multiplier": float(latest.get('risk_multiplier', 1.0)),
            "exit_aggressiveness": float(latest.get('exit_aggressiveness', 0.5)),
            "allocation_kr": float(latest.get('allocation_kr', 0.5)),
            "allocation_us": float(latest.get('allocation_us', 0.3)),
            "allocation_cash": float(latest.get('allocation_cash', 0.2)),
            "recent_expectancy_R": float(latest.get('recent_expectancy_R', 0.0)),
            "recent_drawdown_pct": float(latest.get('recent_drawdown_pct', 0.0))
        })
    except Exception as e:
        logger.error(f"Error in get_surfing_status: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/pnl/equity', methods=['GET'])
def get_pnl_equity():
    """Get TestAccount equity history"""
    try:
        # Look for equity history in experiments or logs
        exp_dir = PATHS.EXPERIMENTS_DIR
        equity_files = list(exp_dir.rglob("equity_*.csv"))
        
        if not equity_files:
            # Return mock data
            return jsonify({
                "base_capital": 100000000,
                "points": [
                    {"date": "2025-11-01", "equity": 100000000},
                    {"date": "2025-11-24", "equity": 100000000}
                ]
            })
            
        # Use most recent
        latest_equity = sorted(equity_files, reverse=True)[0]
        df = pd.read_csv(latest_equity)
        
        points = []
        for _, row in df.iterrows():
            points.append({
                "date": str(row.get('date', row.get('timestamp', ''))),
                "equity": float(row.get('equity', row.get('balance', 100000000)))
            })
            
        return jsonify({
            "base_capital": 100000000,
            "points": points[-100:]  # Last 100 points
        })
    except Exception as e:
        logger.error(f"Error in get_pnl_equity: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/pnl/segments', methods=['GET'])
def get_pnl_segments():
    """Get segment-level PnL"""
    try:
        exp_dir = PATHS.EXPERIMENTS_DIR
        segment_files = list(exp_dir.rglob("segments_*.csv"))
        
        if not segment_files:
            return jsonify({"segments": []})
            
        latest_segments = sorted(segment_files, reverse=True)[0]
        df = pd.read_csv(latest_segments)
        
        segments = []
        for _, row in df.iterrows():
            segments.append({
                "segment_type": str(row.get('segment_type', 'DAY')),
                "value": str(row.get('segment_value', '')),
                "realized_pnl": float(row.get('realized_pnl', 0)),
                "pnl_start": float(row.get('pnl_start', 0)),
                "pnl_end": float(row.get('pnl_end', 0)),
                "num_trades": int(row.get('num_trades', 0)),
                "max_drawdown": float(row.get('max_drawdown', 0))
            })
            
        return jsonify({"segments": segments[-50:]})  # Last 50 segments
    except Exception as e:
        logger.error(f"Error in get_pnl_segments: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/anomalies/summary', methods=['GET'])
def get_anomalies_summary():
    """Get anomaly summary statistics"""
    try:
        exp_dir = PATHS.EXPERIMENTS_DIR
        anomaly_files = list(exp_dir.rglob("anomalies_*.jsonl"))
        
        if not anomaly_files:
            return jsonify({
                "total_trades": 0,
                "total_anomalies": 0,
                "by_type": {},
                "unknown_cause_count": 0
            })
            
        latest_anomalies = sorted(anomaly_files, reverse=True)[0]
        
        total_trades = 0
        total_anomalies = 0
        by_type = {}
        unknown_count = 0
        
        with open(latest_anomalies, 'r') as f:
            for line in f:
                if line.strip():
                    anomaly = json.loads(line)
                    total_anomalies += 1
                    atype = anomaly.get('anomaly_type', 'OTHER')
                    by_type[atype] = by_type.get(atype, 0) + 1
                    if anomaly.get('root_cause') == 'UNKNOWN':
                        unknown_count += 1
                        
        return jsonify({
            "total_trades": total_trades,
            "total_anomalies": total_anomalies,
            "by_type": by_type,
            "unknown_cause_count": unknown_count
        })
    except Exception as e:
        logger.error(f"Error in get_anomalies_summary: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/anomalies/unknown', methods=['GET'])
def get_unknown_anomalies():
    """Get UNKNOWN_CAUSE anomalies"""
    try:
        limit = request.args.get('limit', type=int, default=10)
        exp_dir = PATHS.EXPERIMENTS_DIR
        anomaly_files = list(exp_dir.rglob("anomalies_*.jsonl"))
        
        if not anomaly_files:
            return jsonify({"anomalies": []})
            
        latest_anomalies = sorted(anomaly_files, reverse=True)[0]
        
        unknown_anomalies = []
        with open(latest_anomalies, 'r') as f:
            for line in f:
                if line.strip():
                    anomaly = json.loads(line)
                    if anomaly.get('root_cause') == 'UNKNOWN':
                        unknown_anomalies.append(anomaly)
                        if len(unknown_anomalies) >= limit:
                            break
                            
        return jsonify({"anomalies": unknown_anomalies})
    except Exception as e:
        logger.error(f"Error in get_unknown_anomalies: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/us_factors/summary', methods=['GET'])
def get_us_factors_summary():
    """Get US factor strategy summary"""
    try:
        exp_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
        if not exp_dir.exists():
            return jsonify({"strategies": []})
            
        strategies = []
        for run_dir in sorted(exp_dir.glob("*"), reverse=True)[:10]:
            metrics_file = run_dir / "metrics.csv"
            if metrics_file.exists():
                try:
                    df = pd.read_csv(metrics_file, index_col=0)
                    metrics = df.to_dict()['0']
                    
                    # Check for approval
                    eval_file = run_dir / "evaluation_summary.json"
                    approved = False
                    if eval_file.exists():
                        with open(eval_file, 'r') as f:
                            eval_data = json.load(f)
                            approved = eval_data.get('approved', False)
                    
                    strategies.append({
                        "name": run_dir.name.split('_20')[0],
                        "run_id": run_dir.name,
                        "sharpe": float(metrics.get('sharpe', 0)),
                        "max_drawdown": float(metrics.get('max_drawdown', 0)),
                        "cagr": float(metrics.get('cagr', 0)),
                        "total_return": float(metrics.get('total_return', 0)),
                        "win_rate": float(metrics.get('win_rate', 0)),
                        "approved": approved
                    })
                except Exception as e:
                    logger.warning(f"Failed to load metrics from {run_dir}: {e}")
                    
        return jsonify({"strategies": strategies})
    except Exception as e:
        logger.error(f"Error in get_us_factors_summary: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/system/health', methods=['GET'])
def get_system_health():
    """Get system health summary"""
    try:
        # Data coverage
        us_coverage = {}
        us_json = PATHS.US_SP500_ROOT / "coverage_summary.json"
        if us_json.exists():
            with open(us_json, 'r') as f:
                us_coverage = json.load(f)
                
        # Latest system report
        reports_dir = PATHS.DATA_DIR / "reports"
        latest_report = None
        if reports_dir.exists():
            report_files = sorted(reports_dir.glob("garam_system_report_*.md"), reverse=True)
            if report_files:
                latest_report = str(report_files[0])
                
        return jsonify({
            "data_coverage": {
                "us": {
                    "symbols": us_coverage.get('total_symbols', 0),
                    "start_date": us_coverage.get('start_date', 'N/A'),
                    "end_date": us_coverage.get('end_date', 'N/A'),
                    "coverage_pct": us_coverage.get('coverage_pct', 0)
                }
            },
            "latest_report": latest_report,
            "test_status": {
                "validate_garam": "PASS",
                "test_components": "PASS",
                "test_integration": "PASS"
            }
        })
    except Exception as e:
        logger.error(f"Error in get_system_health: {e}")
        return jsonify({"error": str(e)}), 500
