"""
GARAM Telegram AI Agent
Gemini AI와 직접 대화 - 고급 유지보수 및 분석
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import requests
import json

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GaramAIAgent:
    """
    Gemini AI 에이전트 - 텔레그램을 통한 GARAM 시스템 관리
    
    기능:
    1. 자연어로 복잡한 요청 처리
    2. 로그 분석, 성과 분석, 문제 진단
    3. 설정 변경, 파라미터 튜닝
    4. 승인 시스템 (텔레그램 버튼)
    """
    
    def __init__(self):
        self.bot_token = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        self.gemini_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyA5hG5SO2ygRnhKyPgROev977AVO5u2UjU')
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # System context
        self.system_context = """당신은 GARAM 거래 시스템을 관리하는 AI 전문가입니다.

**역할**:
- 시스템 분석 및 진단
- 성과 분석 및 리포트
- 설정 변경 및 최적화
- 문제 해결 및 유지보수

**가능한 작업**:
1. 로그 분석 (logs/에서 파일 읽기)
2. 백테스트 결과 분석
3. V2 파라미터 조정
4. 긴급 조치 (Kill Switch, 설정 변경)
5. 성과 리포트 생성

**응답 형식** (JSON):
{
  "analysis": "분석 내용",
  "action_required": true/false,
  "actions": ["파일 읽기", "설정 변경" 등],
  "needs_approval": true/false,
  "response": "사용자에게 보여줄 메시지"
}

**규칙**:
- 설정 변경, MDD 초과 조치는 반드시 승인 필요
- 단순 조회/분석은 즉시 실행
- 복잡한 요청은 단계별 설명
"""
    
    def send_message(self, message, parse_mode='Markdown'):
        """Telegram 메시지 전송"""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def send_approval_request(self, action, reason, preview=""):
        """승인 요청 (버튼 포함)"""
        message = f"""
🔔 *승인 요청*

**액션**: {action}
**사유**: {reason}

{preview}

승인하시겠습니까?
        """
        
        buttons = [
            [
                {'text': '✅ 승인', 'callback_data': f'approve_{action}'},
                {'text': '❌ 거부', 'callback_data': 'reject'}
            ]
        ]
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'reply_markup': {'inline_keyboard': buttons}
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Approval request error: {e}")
            return False
    
    def ask_gemini(self, user_message, conversation_history=""):
        """Gemini AI에게 질문"""
        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            
            prompt = f"""{self.system_context}

**대화 기록**:
{conversation_history}

**사용자 요청**: {user_message}

**시스템 정보**:
- 프로젝트 경로: c:/garam/garam
- 로그 경로: c:/garam/garam/logs
- 설정 파일: config/turbo_overlay_config.yaml
- V2 엔진: engine/turbo_overlay.py

JSON 형식으로 응답하세요.
"""
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(
                f"{url}?key={self.gemini_key}",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['candidates'][0]['content']['parts'][0]['text']
                
                # JSON 파싱
                content = content.strip()
                if '```' in content:
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                return json.loads(content)
            else:
                logger.error(f"Gemini API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None
    
    def handle_complex_request(self, user_message):
        """복잡한 요청 처리"""
        logger.info(f"🧠 AI 처리: {user_message}")
        
        # Gemini에게 요청
        result = self.ask_gemini(user_message)
        
        if not result:
            # Gemini실패 시 fallback 응답
            fallback_msg = f"""💬 요청을 받았습니다: "{user_message}"

현재 AI 처리가 일시적으로 불가능합니다.

**대신 사용 가능한 명령**:
- `/status` - 시스템 상태
- `/help` - 도움말

또는 구체적인 질문을 다시 해주세요!"""
            
            self.send_message(fallback_msg)
            return
        
        # 응답 분석
        analysis = result.get('analysis', '')
        action_required = result.get('action_required', False)
        needs_approval = result.get('needs_approval', False)
        response_text = result.get('response', '분석 완료')
        
        # 사용자에게 전송
        if needs_approval:
            # 승인 요청
            action = result.get('action', 'unknown')
            self.send_approval_request(
                action=action,
                reason=analysis,
                preview=response_text
            )
        else:
            # 즉시 응답
            self.send_message(f"🧠 *AI 분석*\n\n{response_text}")
        
        # 액션 실행 (승인 후)
        if action_required and not needs_approval:
            self.execute_actions(result.get('actions', []))
    
    def execute_actions(self, actions):
        """액션 실행"""
        for action in actions:
            logger.info(f"🔧 실행: {action}")
            # TODO: 실제 액션 구현
            # - 파일 읽기
            # - 설정 변경
            # - 백테스트 실행 등


# Global instance
_ai_agent = None

def get_ai_agent():
    global _ai_agent
    if _ai_agent is None:
        _ai_agent = GaramAIAgent()
    return _ai_agent


if __name__ == "__main__":
    # Test
    agent = GaramAIAgent()
    
    # Test complex request
    agent.handle_complex_request("9월에 손실이 난 원인을 분석해줘")
