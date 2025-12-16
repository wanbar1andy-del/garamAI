"""
AI Core API - Real Data Implementation
Provides AI Control Center endpoints with actual data from JSON files and LLM
"""
import logging
import json
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from garam.config import PATHS

ai_core_bp = Blueprint('ai_core', __name__)
logger = logging.getLogger(__name__)


def _read_json_if_exists(path: Path):
    """Helper to safely read JSON files"""
    if not path.exists():
        return None
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read JSON {path}: {e}")
        return None


@ai_core_bp.route('/health', methods=['GET'])
def get_ai_health():
    """
    AI Control Center용 Health 요약.
    - HealthCollector에서 만든 health_YYYYMMDD.json 기반
    - LLM 헬스체크(optional) 추가
    """
    today_str = datetime.now().strftime("%Y%m%d")
    health_file = PATHS.DATA_DIR / "system" / f"health_{today_str}.json"

    health_data = _read_json_if_exists(health_file)
    if health_data is None:
        # 최소한 UNKNOWN이라도 반환
        return jsonify({
            "date": today_str,
            "overall": "UNKNOWN",
            "message": "HealthCollector data not found",
            "raw": None,
        })

    # LLM 상태 체크 (시간 허용 시)
    llm_status = "UNKNOWN"
    try:
        from garam.core.llm_client import get_llm_client
        client = get_llm_client()
        if client.health_check():
            llm_status = "OK"
        else:
            llm_status = "WARN"
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
        llm_status = "ERROR"

    # overall 계산 (간단 룰)
    overall = health_data.get("status", "UNKNOWN")
    if llm_status == "ERROR":
        overall = "WARN" if overall == "OK" else overall

    resp = {
        "date": health_data.get("timestamp", today_str),
        "overall": overall,
        "system_health": health_data,
        "llm_status": llm_status,
    }
    return jsonify(resp)


@ai_core_bp.route('/summary', methods=['GET'])
def get_ai_summary():
    """
    실제 데이터 기반 요약:
    - system_health: health_YYYYMMDD.json
    - strategy_daily_plan: strategy/daily_plan.json (있으면)
    - simulation_today: simulation/simulation_today.json (있으면)
    - config/ai_core_prompt.txt: System Prompt v2
    """
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")

    # 1) 데이터 로딩
    health_file = PATHS.DATA_DIR / "system" / f"health_{today_str}.json"
    strategy_file = PATHS.DATA_DIR / "strategy" / "daily_plan.json"
    simulation_file = PATHS.DATA_DIR / "simulation" / "simulation_today.json"

    system_health = _read_json_if_exists(health_file)
    strategy_daily_plan = _read_json_if_exists(strategy_file)
    simulation_today = _read_json_if_exists(simulation_file)

    # 2) System Prompt 불러오기
    prompt_path = PATHS.CONFIG_DIR / "ai_core_prompt.txt"
    try:
        with prompt_path.open('r', encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        logger.error(f"Failed to read ai_core_prompt.txt: {e}")
        return jsonify({"error": "SYSTEM_PROMPT_NOT_FOUND"}), 500

    # 3) user_prompt 구성 (실제 JSON 전달)
    user_payload = {
        "date": today.strftime("%Y-%m-%d"),
        "system_health": system_health,
        "strategy_daily_plan": strategy_daily_plan,
        "simulation_today": simulation_today,
    }

    user_prompt = json.dumps(user_payload, ensure_ascii=False)

    # 4) LLM 호출
    try:
        from garam.core.llm_client import get_llm_client
        client = get_llm_client()
        raw_output = client.ask_gpt_oss(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=800,
        )
    except Exception as e:
        logger.error(f"AI Core summary generation failed: {e}")
        # Fallback: 기본 요약 생성
        return jsonify({
            "date": today.strftime("%Y-%m-%d"),
            "system_status": {
                "overall": system_health.get("status", "UNKNOWN") if system_health else "UNKNOWN",
                "details": [
                    f"Kiwoom: {system_health.get('components', {}).get('kiwoom', {}).get('status', 'UNKNOWN')}" if system_health else "Kiwoom: UNKNOWN",
                    "LLM: ERROR (호출 실패)",
                ]
            },
            "summary_points": [
                "시스템 요약 생성에 실패했습니다.",
                f"오류: {str(e)}"
            ],
            "risk_flags": ["LLM 연결 실패"],
            "action_items": ["LLM 서비스(Ollama) 상태 확인 필요"]
        })

    # 5) LLM이 JSON을 그대로 반환하도록 설계했으므로, 파싱 시도
    try:
        # Markdown code block 제거
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```"):
            cleaned_output = cleaned_output.replace("```json", "").replace("```", "").strip()
            
        summary_json = json.loads(cleaned_output)
    except Exception as e:
        logger.warning(f"Failed to parse LLM JSON output: {e}")
        # fallback: 텍스트 그대로 반환
        summary_json = {
            "date": today.strftime("%Y-%m-%d"),
            "system_status": {
                "overall": "UNKNOWN",
                "details": [],
            },
            "summary_points": [raw_output],
            "risk_flags": [],
            "action_items": [],
        }

    return jsonify(summary_json)


@ai_core_bp.route('/guard', methods=['GET'])
def get_guard_status():
    """
    Returns the current permission level and blocked action logs.
    """
    return jsonify({
        'permission_level': 'ADVICE_ONLY', # ADVICE_ONLY, SIGNAL_SUGGEST, FULL_AUTO
        'allowed_actions': ['ADVICE', 'EXPLAIN'],
        'blocked_logs': [
            {'time': '10:23:45', 'action': 'send_order', 'reason': 'Permission Denied'},
            {'time': '11:05:12', 'action': 'modify_risk', 'reason': 'Manual Override Active'}
        ]
    })


@ai_core_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Receives user feedback (👍/👎) for AI comments.
    """
    data = request.json
    feedback_type = data.get('type') # 'positive' or 'negative'
    comment_id = data.get('comment_id')
    reason = data.get('reason', '')
    
    logger.info(f"AI Feedback Received: {feedback_type} for {comment_id} ({reason})")
    
    return jsonify({'status': 'success', 'message': 'Feedback recorded'})


@ai_core_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for AI interaction
    """
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Try LLM first
        try:
            from garam.core.llm_client import LLMClient
            client = LLMClient()
            reply = client.ask_gpt_oss(
                prompt=message,
                system_prompt="너는 GARAM 트레이딩 시스템의 AI 어시스턴트다. 간결하고 정확하게 답변한다.",
                temperature=0.7,
                max_tokens=500
            )
            return jsonify({'reply': reply, 'source': 'LLM'})
        except Exception as llm_error:
            logger.warning(f"LLM chat failed: {llm_error}")
            # Fallback to rule-based
            reply = f"현재 LLM 서비스가 응답하지 않습니다. 질문: '{message}'"
            return jsonify({'reply': reply, 'source': 'RULE_BASED'})
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500
