from flask import Blueprint, jsonify, request
import pandas as pd
import json
from pathlib import Path
import logging
from datetime import datetime

from config import PATHS

metrics_bp = Blueprint('metrics', __name__)
logger = logging.getLogger(__name__)

def get_latest_experiment_file(exp_type: str, file_pattern: str):
    """Find the latest experiment file"""
    if exp_type == "kr_intraday":
        base_dir = PATHS.EXPERIMENTS_DIR / "kr_intraday"
    elif exp_type == "portfolio":
        base_dir = PATHS.EXPERIMENTS_DIR / "portfolio"
    else:
        return None
        
    if not base_dir.exists():
        return None
        
    files = list(base_dir.glob(file_pattern))
    if not files:
        return None
        
    # Sort by modification time
    latest_file = sorted(files, key=lambda x: x.stat().st_mtime)[-1]
    return latest_file

@metrics_bp.route('/kr/performance/summary', methods=['GET'])
def get_kr_performance_summary():
    """Get latest KR Intraday performance summary"""
    try:
        latest_file = get_latest_experiment_file("kr_intraday", "performance_*.json")
        
        if not latest_file:
            return jsonify({"error": "No performance data found"}), 404
            
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error serving KR summary: {e}")
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get latest Integrated Portfolio performance summary"""
    # Note: Portfolio report is currently Markdown. 
    # We should probably update the simulation script to save JSON as well.
    # For now, let's try to parse the report or check if we can save JSON in the sim script.
    # Actually, let's update the sim script to save JSON first.
    # But to avoid blocking, let's check if we can serve the daily metrics which are in the report?
    # No, let's assume we will update the sim script or just serve a placeholder if JSON missing.
    
    # Wait, I didn't update the sim script to save JSON in NP-2.
    # I should probably do that quickly or parse the markdown? 
    # Parsing markdown is brittle.
    # Let's check if I can quickly update the sim script to save JSON.
    # Or I can just serve the daily_pnl csv and calculate summary on the fly here?
    # That's better.
    
    try:
        # Try to find the latest portfolio report to get the ID
        latest_report = get_latest_experiment_file("portfolio", "portfolio_report_*.md")
        if not latest_report:
             return jsonify({"error": "No portfolio data found"}), 404
             
        # Extract ID from filename: portfolio_report_20251125_190804.md
        run_id = latest_report.stem.replace("portfolio_report_", "")
        
        # We don't have a JSON summary file yet. 
        # But we have the KR and US P&L files that were used? No, those are inputs.
        # The simulation output was only the markdown report.
        
        # CORRECTIVE ACTION: I should have saved JSON in NP-2.
        # For now, I will return a dummy response or error, and I will update the sim script in the next step.
        return jsonify({
            "status": "JSON summary not implemented yet. Please run simulation with JSON output enabled."
        })
        
    except Exception as e:
        logger.error(f"Error serving portfolio summary: {e}")
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/portfolio/daily_pnl', methods=['GET'])
def get_portfolio_daily_pnl():
    """Get daily P&L time series for charting"""
    # This also requires the simulation to save a CSV/JSON of daily metrics.
    # In NP-2, I only saved a Markdown report.
    # I need to update the simulation script to save `daily_metrics.csv` or similar.
    return jsonify([])
