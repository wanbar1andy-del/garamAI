from flask import Blueprint, jsonify
from garam.config import PATHS
import json

strategy_bp = Blueprint("strategy", __name__)

@strategy_bp.route("/daily_plan", methods=["GET"])
def get_daily_plan():
    """
    오늘 장에 대한 전략 요약 (Daily Playbook)
    - 나중에 전략엔진이 만든 json을 그대로 읽어 반환
    - 지금은 Dummy or NO_DATA
    """
    try:
        plan_file = PATHS.STRATEGY_DAILY_PLAN
        if not plan_file.exists():
            return jsonify({"status": "NO_DATA", "message": "daily_plan not generated"}), 200

        data = plan_file.read_text(encoding="utf-8")
        # 이미 json이면 그대로 반환, 아니면 parse 후 반환
        return jsonify(json.loads(data))
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@strategy_bp.route("/signals/live", methods=["GET"])
def get_live_signals():
    """
    실시간/오늘 유효한 시그널 리스트
    """
    try:
        live_file = PATHS.STRATEGY_SIGNALS_LIVE
        if not live_file.exists():
            return jsonify({"status": "NO_DATA", "signals": []}), 200

        signals = json.loads(live_file.read_text(encoding="utf-8"))
        return jsonify({"status": "OK", "signals": signals}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@strategy_bp.route("/signals/history", methods=["GET"])
def get_signals_history():
    """
    과거 N개 시그널 히스토리 (옵션)
    - 초기에는 간단히 하나의 history.json에서 읽기
    - 나중에 DB나 파일 롤링으로 교체
    """
    try:
        history_file = PATHS.STRATEGY_SIGNALS_HISTORY
        if not history_file.exists():
            return jsonify({"status": "NO_DATA", "signals": []}), 200

        signals = json.loads(history_file.read_text(encoding="utf-8"))
        return jsonify({"status": "OK", "signals": signals}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500
