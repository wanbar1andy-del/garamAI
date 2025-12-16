from flask import Blueprint, jsonify, current_app
import json
from pathlib import Path

# garam.config 에서 PATHS 가져오기
try:
    from garam.config import PATHS
except ImportError:
    # 안전장치: 개발 시 혹시 모를 Import 오류
    PATHS = None

simulation_bp = Blueprint("simulation_bp", __name__)
print(f"[DEBUG] Simulation API Loaded. Blueprint: {simulation_bp}")

def _load_simulation_today():
    """
    PATHS.TODAY_SIM_FILE 에서 오늘 시뮬레이션 결과를 읽어온다.
    파일이 없으면 None 반환.
    """
    if PATHS is None:
        current_app.logger.error("[SimulationAPI] PATHS not available")
        return None

    sim_path: Path = PATHS.TODAY_SIM_FILE

    if not sim_path.exists():
        return None

    try:
        with sim_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        current_app.logger.error(f"[SimulationAPI] Failed to load simulation file: {e}")
        return None


@simulation_bp.route("/today", methods=["GET"])
def get_simulation_today():
    """
    GET /api/simulation/today
    - 파일이 있으면 해당 JSON 그대로 반환
    - 없으면 status=NO_DATA
    """
    data = _load_simulation_today()
    if data is None:
        return jsonify({
            "status": "NO_DATA",
            "message": "simulation_today.json not found"
        }), 200

    # data 안에 status 필드가 없으면 기본값 추가
    if "status" not in data:
        data["status"] = "OK"

    return jsonify(data), 200

@simulation_bp.route("/history", methods=["GET"])
def get_simulation_history():
    """
    GET /api/simulation/history
    - PATHS.ACCOUNT_SNAPSHOT (csv)를 읽어서 차트용 데이터 반환
    - [ {timestamp, total_equity}, ... ]
    """
    if PATHS is None:
        return jsonify([]), 500

    csv_path = PATHS.ACCOUNT_SNAPSHOT
    if not csv_path.exists():
        return jsonify([]), 200

    result = []
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        # 필요한 컬럼만 추출 (timestamp, total_equity)
        # CSV 컬럼명이 정확한지 확인 필요하지만, 보통 timestamp, total_equity로 저장됨
        if 'timestamp' in df.columns and 'total_equity' in df.columns:
            # 날짜 오름차순 정렬
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)
            
            for _, row in df.iterrows():
                result.append({
                    "timestamp": str(row['timestamp']),
                    "total_equity": float(row['total_equity'])
                })
    except Exception as e:
        current_app.logger.error(f"[SimulationAPI] History load error: {e}")
        return jsonify([]), 500

    return jsonify(result), 200

@simulation_bp.route("/comparison", methods=["GET"])
def get_simulation_comparison():
    """
    GET /api/simulation/comparison
    - account_snapshot.csv에 기록된 daily_return, engine1_ret, engine2_ret를 사용하여
    - 가상의 Engine 1/2 Equity Curve를 재구성하여 반환.
    - { 
        "dates": [...], 
        "blended": [...], 
        "engine1": [...], 
        "engine2": [...] 
    }
    """
    if PATHS is None:
        return jsonify({}), 500
        
    csv_path = PATHS.ACCOUNT_SNAPSHOT
    if not csv_path.exists():
        return jsonify({}), 200
        
    try:
        import pandas as pd
        import numpy as np
        
        df = pd.read_csv(csv_path)
        if df.empty:
            return jsonify({}), 200
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values('timestamp', inplace=True)
        
        # Initial Capital from total_equity start
        initial_capital = df.iloc[0]['total_equity']
        
        e1_curve = [initial_capital]
        e2_curve = [initial_capital]
        kospi_curve = [initial_capital]
        
        dates = [str(df.iloc[0]['timestamp'])]
        blended = [float(df.iloc[0]['total_equity'])]
        
        # Skip first row if returns are not applicable to the first day's open
        # But our simulation logs daily returns for that day.
        # Assuming total_equity at row i is AFTER daily_return of row i.
        
        # Let's reconstruct.
        # total_equity[i] = total_equity[i-1] * (1+daily_ret[i])
        # We want to show curves starting from same point.
        
        # Pre-check columns
        if not {'engine1_ret', 'engine2_ret'}.issubset(df.columns):
            # If detailed columns missing, just return blended
            return jsonify({
                "dates": df['timestamp'].astype(str).tolist(),
                "blended": df['total_equity'].tolist(),
                "engine1": [],
                "engine2": []
            }), 200
            
        # Reconstruct E1/E2
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_e1 = e1_curve[-1]
            prev_e2 = e2_curve[-1]
            
            # Simple compounding
            curr_e1 = prev_e1 * (1.0 + row['engine1_ret'])
            curr_e2 = prev_e2 * (1.0 + row['engine2_ret'])
            
            e1_curve.append(curr_e1)
            e2_curve.append(curr_e2)
            
            # KOSPI Curve (if available, else flat)
            if 'market_ret' in df.columns:
                prev_kospi = kospi_curve[-1] if 'kospi_curve' in locals() else initial_capital
                curr_kospi = prev_kospi * (1.0 + row['market_ret'])
            else:
                curr_kospi = initial_capital
            
            if 'kospi_curve' not in locals():
                kospi_curve = [initial_capital, curr_kospi]
            else:
                kospi_curve.append(curr_kospi)
            
            dates.append(str(row['timestamp']))
            blended.append(float(row['total_equity']))
            
        return jsonify({
            "dates": dates,
            "blended": blended,
            "engine1": e1_curve,
            "engine2": e2_curve,
            "kospi": kospi_curve
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"[SimulationAPI] Comparison error: {e}")
        return jsonify({"error": str(e)}), 500
