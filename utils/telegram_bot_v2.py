"""
GARAM Telegram Bot with Natural Language Processing
GPT 기반 자연어 명령 처리
"""

import os
import sys
import logging
import requests
from datetime import datetime
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GaramTelegramBotV2:
    """
    GARAM Telegram Bot with GPT Integration
    
    기능:
    1. 자연어 명령 처리 (GPT)
    2. Intent 인식 및 자동 실행
    3. 명령어 암기 불필요
    """
    
    def __init__(self, bot_token=None, chat_id=None, gemini_api_key=None):
        self.bot_token = bot_token or os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY') or 'AIzaSyA5hG5SO2ygRnhKyPgROev977AVO5u2UjU'
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram bot enabled with Gemini AI")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.pending_approvals = {}
        
        # Gemini System Prompt
        self.system_prompt = """당신은 GARAM 거래 시스템을 제어하는 AI입니다.

사용자 메시지를 분석해서 JSON으로 응답하세요:

명령 종류:
- status: 상태 확인 (예: "상태 어때?", "지금 뭐해?")
- kill: 긴급 중단 (예: "멈춰!", "중단!", "팔아!")
- restart: 재시작 (예: "다시 시작", "재시작")
- help: 도움말 (예: "뭘 할 수 있어?")
- chat: 일반 대화 (명령과 관련 없음)

응답 형식:
{
  "intent": "status|kill|restart|help|chat",
  "confidence": 0.0-1.0,
  "needs_confirmation": true/false,
  "response": "사용자에게 보여줄 메시지"
}

규칙:
- kill은 항상 needs_confirmation: true
- confidence < 0.7이면 재확인
- 일반 대화는 intent: "chat", 친절하게 응답
"""
    
    def send_message(self, message, level='info', parse_mode='Markdown'):
        """텔레그램 메시지 송신"""
        if not self.enabled:
            return False
        
        emoji_map = {
            'info': '✅',
            'warning': '⚠️',
            'critical': '🚨',
            'success': '✅',
            'error': '❌'
        }
        
        emoji = emoji_map.get(level, '📢')
        formatted_message = f"{emoji} *GARAM*\n\n{message}"
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def send_keyboard(self, message, buttons):
        """인라인 키보드 메시지"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'reply_markup': {
                    'inline_keyboard': buttons
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Keyboard error: {e}")
            return False
    
    def get_updates(self, offset=None):
        """
        업데이트 가져오기 (명령 수신)
        
        Args:
            offset: 업데이트 offset
        
        Returns:
            updates: 업데이트 리스트
        """
        if not self.enabled:
            return []
        
        try:
            url = f"{self.api_url}/getUpdates"
            params = {'timeout': 10}
            if offset:
                params['offset'] = offset
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Get updates error: {e}")
            return []
    
    def handle_command(self, command, args=''):
        """
        전통적 명령 처리 (fallback)
        
        Commands:
        /status - 시스템 상태
        /kill - 긴급 중단
        /restart - 재시작
        /help - 도움말
        """
        command = command.lower()
        
        if command == '/status':
            return self.cmd_status()
        
        elif command == '/kill':
            return self.cmd_kill_switch()
        
        elif command == '/restart':
            return self.cmd_restart()
        
        elif command == '/help':
            return self.cmd_help()
        
        else:
            self.send_message(f"알 수 없는 명령: {command}\n/help 로 도움말 확인", 'warning')
            return f"Unknown command: {command}"
    
    def parse_natural_language(self, user_message):
        """
        Gemini로 자연어 명령 파싱
        
        Args:
            user_message: 사용자 메시지
            
        Returns:
            dict: {intent, confidence, needs_confirmation, response}
        """
        if not self.gemini_api_key:
            logger.warning("Gemini API key not set, using fallback parser")
            return self.fallback_parser(user_message)
        
        try:
            # Gemini API 호출
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{self.system_prompt}\n\n사용자 메시지: {user_message}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 200
                }
            }
            
            response = requests.post(
                f"{url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['candidates'][0]['content']['parts'][0]['text']
                
                # JSON 파싱
                # Gemini가 ```json ``` 으로 감쌀 수 있음
                content = content.strip()
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                result = json.loads(content)
                
                logger.info(f"Gemini parsed: {user_message} → {result.get('intent', 'unknown')}")
                
                return result
            else:
                logger.error(f"Gemini API error: {response.status_code}")
                return self.fallback_parser(user_message)
            
        except Exception as e:
            logger.error(f"GPT parsing error: {e}")
            return self.fallback_parser(user_message)
    
    def fallback_parser(self, user_message):
        """
        Gemini 없이 간단한 키워드 매칭 (Fallback)
        """
        msg = user_message.lower()
        
        # Kill switch keywords (최우선)
        kill_keywords = ['멈춰', '중단', '정지', 'stop', 'kill', '긴급', '팔아', '청산', '강제']
        if any(kw in msg for kw in kill_keywords):
            return {
                'intent': 'kill',
                'confidence': 0.9,
                'needs_confirmation': True,
                'response': '⚠️ 긴급 중단 명령을 감지했습니다. 확실합니까?'
            }
        
        # Status keywords
        status_keywords = ['상태', 'status', '어때', '어떻게', '정상', '확인', '뭐해', '작동']
        if any(kw in msg for kw in status_keywords):
            return {
                'intent': 'status',
                'confidence': 0.9,
                'needs_confirmation': False,
                'response': '시스템 상태를 확인합니다...'
            }
        
        # Restart keywords
        restart_keywords = ['재시작', 'restart', '리셋', 'reset', '다시']
        if any(kw in msg for kw in restart_keywords):
            return {
                'intent': 'restart',
                'confidence': 0.8,
                'needs_confirmation': True,
                'response': '시스템 재시작을 확인합니다. 진행할까요?'
            }
        
        # Help keywords
        help_keywords = ['도움', 'help', '사용법', '뭘', '명령', '기능']
        if any(kw in msg for kw in help_keywords):
            return {
                'intent': 'help',
                'confidence': 1.0,
                'needs_confirmation': False,
                'response': '명령어 목록을 보여드릴게요.'
            }
        
        # 기본값: 모든 것을 chat으로 처리 (제한 없음!)
        return {
            'intent': 'chat',
            'confidence': 1.0,
            'needs_confirmation': False,
            'response': f'안녕하세요! "{user_message}" 잘 받았습니다.\n\n'
                       f'GARAM 시스템을 도와드리고 있어요.\n\n'
                       f'필요하시면 "상태 확인", "도움말" 같은 명령을 주세요!'
        }
    
    def handle_natural_message(self, user_message):
        """
        자연어 메시지 처리
        
        사용자 예시:
        - "지금 상태 어때?" → status 실행
        - "전부 멈춰!" → kill 확인 요청
        - "다시 시작해줘" → restart 확인 요청
        - "안녕?" → 대화
        """
        # Gemini로 intent 파싱
        result = self.parse_natural_language(user_message)
        
        intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0.0)
        needs_confirmation = result.get('needs_confirmation', False)
        response_text = result.get('response', '이해하지 못했습니다.')
        
        # Chat intent (일반 대화)
        if intent == 'chat':
            self.send_message(response_text, 'info')
            return
        
        # Unknown intent
        if intent == 'unknown':
            self.send_message(f"💬 {response_text}", 'info')
            return
        
        # Confidence 체크
        if confidence < 0.7:
            self.send_message(
                f"잘 이해하지 못했습니다 (확신도: {confidence:.0%})\n\n"
                f"{response_text}",
                'warning'
            )
            return
        
        # 확인 필요 시 버튼 표시
        if needs_confirmation:
            buttons = [
                [
                    {'text': '✅ 예', 'callback_data': f'confirm_{intent}'},
                    {'text': '❌ 아니오', 'callback_data': 'cancel'}
                ]
            ]
            self.send_keyboard(response_text, buttons)
        else:
            # 즉시 실행
            self.execute_command(intent)
    
    def execute_command(self, intent):
        """명령 실행"""
        if intent == 'status':
            self.cmd_status()
        elif intent == 'kill':
            self.cmd_kill_switch()
        elif intent == 'restart':
            self.cmd_restart()
        elif intent == 'help':
            self.cmd_help()
        else:
            self.send_message("알 수 없는 명령입니다.", 'error')
    
    def cmd_status(self):
        """시스템 상태"""
        try:
            import requests as req
            try:
                resp = req.get('http://localhost:5000/health', timeout=3)
                dashboard = '✅ 정상' if resp.status_code == 200 else '❌ 오류'
            except:
                dashboard = '❌ 오류'
            
            sys.path.insert(0, 'c:/garam')
            from garam.config import PATHS
            kiwoom = '✅ 연결' if PATHS.KIWOOM_FLAG_PATH.exists() else '❌ 미연결'
            
            status = f"""
📊 *시스템 상태*

**Dashboard**: {dashboard}
**Kiwoom**: {kiwoom}
**시각**: {datetime.now().strftime('%H:%M:%S')}
            """
            
            self.send_message(status, 'info')
            
        except Exception as e:
            self.send_message(f"상태 확인 실패: {e}", 'error')
    
    def cmd_kill_switch(self):
        """긴급 중단"""
        self.send_message(
            "🚨 *긴급 중단 활성화*\n\n"
            "모든 거래를 중단합니다...\n"
            "포지션 청산 중...",
            'critical'
        )
        
        # TODO: 실제 중단 로직
        # stop_all_trading()
        # close_all_positions()
    
    def cmd_restart(self):
        """재시작"""
        self.send_message(
            "🔄 *시스템 재시작*\n\n"
            "Dashboard를 재시작합니다...",
            'warning'
        )
        
        # TODO: 실제 재시작
        # restart_dashboard()
    
    def cmd_help(self):
        """도움말"""
        help_text = """
💬 *자연어 명령 지원*

저에게 편하게 말하세요:

**상태 확인**
"상태 어때?", "지금 어떻게 돼?"

**긴급 중단** ⚠️
"멈춰!", "중단!", "전부 팔아!"

**재시작**
"다시 시작해", "재시작해줘"

**달래기**
명령어를 외울 필요 없습니다!
자연스럽게 말하세요.
        """
        
        self.send_message(help_text, 'info')


# Global instance
_telegram_bot_v2 = None

def get_telegram_bot():
    """Get global instance"""
    global _telegram_bot_v2
    if _telegram_bot_v2 is None:
        _telegram_bot_v2 = GaramTelegramBotV2()
    return _telegram_bot_v2


def send_telegram(message, level='info'):
    """Send Telegram message"""
    bot = get_telegram_bot()
    return bot.send_message(message, level)


if __name__ == "__main__":
    # Test
    bot = GaramTelegramBotV2()
    
    if bot.enabled:
        print("Testing natural language...")
        
        # Test natural language parsing
        test_messages = [
            "지금 상태 어때?",
            "전부 멈춰!",
            "다시 시작해줘",
            "도움말"
        ]
        
        for msg in test_messages:
            print(f"\n사용자: {msg}")
            result = bot.parse_natural_language(msg)
            print(f"  → Intent: {result['intent']} ({result['confidence']:.0%})")
        
        print("\n✅ Natural language test complete!")
    else:
        print("❌ Bot not configured")
