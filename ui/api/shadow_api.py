from flask import Blueprint, jsonify, request
from garam.config import PATHS
import json
import logging
from datetime import datetime

shadow_bp = Blueprint('shadow_bp', __name__)
logger = logging.getLogger("ShadowAPI")

@shadow_bp.route('/perf/daily', methods=['GET'])
def get_daily_perf():
    """Get today's shadow performance metrics"""
    try:
        mode = request.args.get('mode', 'SHADOW').upper()
        log_subdir = "live_paper" if mode == "LIVE_PAPER" else "shadow"
        
        perf_file = PATHS.LOGS_DIR / log_subdir / "perf_daily.json"
        
        if not perf_file.exists():
            return jsonify({
                "status": "No Data",
                "total_pnl": 0,
                "win_rate": 0,
                "total_trades": 0
            })
            
        with open(perf_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
            
    except Exception as e:
        logger.error(f"Error serving daily perf: {e}")
        return jsonify({"error": str(e)}), 500

@shadow_bp.route('/trades/today', methods=['GET'])
def get_today_trades():
    """Get today's trade list"""
    try:
        mode = request.args.get('mode', 'SHADOW').upper()
        log_subdir = "live_paper" if mode == "LIVE_PAPER" else "shadow"
        
        date_str = datetime.now().strftime('%Y%m%d')
        trades_file = PATHS.LOGS_DIR / log_subdir / f"trades_{date_str}.json"
        
        if not trades_file.exists():
            return jsonify([])
            
        with open(trades_file, 'r', encoding='utf-8') as f:
            trades = json.load(f)
            # Reverse to show latest first
            return jsonify(trades[::-1])
            
    except Exception as e:
        logger.error(f"Error serving trades: {e}")
        return jsonify({"error": str(e)}), 500
@shadow_bp.route('/signals', methods=['GET'])
def get_recent_signals():
    """Get recent signals from today's log"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # SignalLogger saves to LOGS_DIR/signals
        jsonl_file = PATHS.LOGS_DIR / "signals" / f"signals_{date_str}.jsonl"
        
        if not jsonl_file.exists():
            return jsonify({"signals": []})
            
        signals = []
        # Read last 50 lines
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                try:
                    signals.append(json.loads(line))
                except:
                    continue
                    
        # Reverse to show latest first
        return jsonify({"signals": signals[::-1]})
            
    except Exception as e:
        logger.error(f"Error serving signals: {e}")
        return jsonify({"error": str(e)}), 500
