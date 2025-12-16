from flask import Blueprint, jsonify
import json
from pathlib import Path
import pandas as pd
from datetime import date
from garam.config import PATHS

regime_bp = Blueprint('regime', __name__)

@regime_bp.route('/regime/summary', methods=['GET'])
def get_regime_summary():
    """
    Get 20-year regime summary stats
    """
    try:
        summary_path = PATHS.EXPERIMENTS_DIR / "regime_lab" / "regime_summary.json"
        if not summary_path.exists():
            return jsonify({})
            
        with open(summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@regime_bp.route('/regime/current', methods=['GET'])
def get_current_regime():
    """
    Get current market regime based on latest data
    """
    try:
        # Using KOSPI as default reference
        data_path = PATHS.DATA_ROOT / "history" / "labeled_KR_KOSPI_daily_20y.csv"
        
        if not data_path.exists():
            return jsonify({'regime': 'UNKNOWN', 'date': None})
            
        # Read last line efficiently? For CSV, pandas is easiest but slow for huge files.
        # Since it's 20y daily, it's not that huge (~5000 lines). Pandas is fine.
        df = pd.read_csv(data_path, parse_dates=['timestamp'])
        if df.empty:
             return jsonify({'regime': 'UNKNOWN', 'date': None})
             
        last_row = df.iloc[-1]
        
        return jsonify({
            'regime': last_row['state'],
            'date': last_row['timestamp'].strftime('%Y-%m-%d'),
            'close': float(last_row['close']),
            'change': float(last_row['ret']) if 'ret' in last_row else 0.0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Playbook API ----------

def _get_reports_dir() -> Path:
    return PATHS.DATA_ROOT / "reports"

def _load_playbook_json(as_of: date) -> dict:
    reports_dir = _get_reports_dir()
    # Filename format from regime_playbook.py: regime_playbook_YYYYMMDD.json
    fname = f"regime_playbook_{as_of.strftime('%Y%m%d')}.json"
    path = reports_dir / fname
    if not path.exists():
        raise FileNotFoundError(f"Playbook not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

@regime_bp.route('/regime/playbook/today', methods=['GET'])
def get_today_playbook():
    """Get today's Regime Playbook"""
    as_of = date.today()
    try:
        payload = _load_playbook_json(as_of)
        return jsonify(payload)
    except FileNotFoundError:
        # Try yesterday if today's not ready (optional, but good for UX)
        # For now, just return 404 to encourage generation
        return jsonify({'error': 'Playbook not generated for today'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@regime_bp.route('/regime/playbook/<datestr>', methods=['GET'])
def get_playbook_by_date(datestr: str):
    """Get Regime Playbook by date (YYYY-MM-DD)"""
    try:
        as_of = date.fromisoformat(datestr)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
    try:
        payload = _load_playbook_json(as_of)
        return jsonify(payload)
    except FileNotFoundError:
        return jsonify({'error': 'Playbook not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
