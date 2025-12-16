"""
GARAM Telegram Smart Handler
Gemini API 없이 직접 처리 - 확실하고 빠름
"""

import os
import sys
import logging
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

logger = logging.getLogger(__name__)

class SmartTelegramHandler:
    """
    키워드 기반 스마트 핸들러
    Gemini API 없이 직접 처리
    """
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
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
    
    def handle_message(self, user_message):
        """사용자 메시지 처리"""
        msg = user_message.lower()
        
        # 상태 확인
        if any(kw in msg for kw in ['상태', 'status', '어때', '정상']):
            return self.get_status()
        
        # 로그 확인
        elif any(kw in msg for kw in ['로그', 'log', '기록']):
            return self.get_logs()
        
        # 분석 요청
        elif any(kw in msg for kw in ['분석', '왜', '원인', 'analyze']):
            return self.analyze_request(user_message)
        
        # Kill switch
        elif any(kw in msg for kw in ['멈춰', '중단', 'kill', 'stop']):
            return self.kill_switch()
        
        # 도움말
        elif any(kw in msg for kw in ['도움', 'help', '명령']):
            return self.show_help()
        
        # 일반 대화
        else:
            return self.friendly_chat(user_message)
    
    def get_status(self):
        """시스템 상태"""
        try:
            # Dashboard 체크
            try:
                resp = requests.get('http://localhost:5000/health', timeout=3)
                dashboard = '✅ 정상' if resp.status_code == 200 else '❌ 오류'
            except:
                dashboard = '❌ 미실행'
            
            # Kiwoom 체크
            kiwoom = '✅ 연결' if PATHS.KIWOOM_FLAG_PATH.exists() else '❌ 미연결'
            
            # 시간
            now = datetime.now().strftime('%H:%M:%S')
            
            msg = f"""📊 **GARAM 시스템 상태**

**Dashboard**: {dashboard}
**Kiwoom**: {kiwoom}
**시각**: {now}

✅ 시스템 작동 중"""
            
            self.send_message(msg)
            return "Status sent"
            
        except Exception as e:
            self.send_message(f"❌ 상태 확인 실패: {e}")
            return f"Error: {e}"
    
    def get_logs(self):
        """최근 로그"""
        try:
            log_file = Path('c:/garam/garam/logs/telegram_conversation.log')
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent = ''.join(lines[-20:])  # 최근 20줄
                
                msg = f"""📝 **최근 로그**

```
{recent[:3000]}
```

더 보려면: "로그 상세" 입력"""
                
                self.send_message(msg)
                return "Logs sent"
            else:
                self.send_message("❌ 로그 파일이 없습니다.")
                return "No logs"
                
        except Exception as e:
            self.send_message(f"❌ 로그 읽기 실패: {e}")
            return f"Error: {e}"
    
    def analyze_request(self, message):
        """분석 요청"""
        msg = f"""🔍 **분석 요청 받음**

요청: "{message}"

**현재 가능한 간단한 분석**:
1. "9월 로그" → 9월 거래 내역
2. "최근 성과" → 최근 수익률
3. "오류 로그" → 에러 기록

**복잡한 분석**은 여기(개발 채팅)에서 요청하세요.
그쪽에서 더 정확한 분석이 가능합니다!"""
        
        self.send_message(msg)
        return "Analysis request acknowledged"
    
    def kill_switch(self):
        """긴급 중단"""
        msg = """🚨 **Kill Switch 확인**

정말 모든 거래를 중단하시겠습니까?

이 기능은 중요하므로 여기(개발 채팅)에서
직접 확인하고 실행하는 것을 권장합니다!

긴급하면: `/kill` 입력"""
        
        self.send_message(msg)
        return "Kill switch confirmation requested"
    
    def show_help(self):
        """도움말"""
        msg = """📚 **GARAM Telegram 도움말**

**간단한 명령**:
- "상태 어때?" → 시스템 상태
- "로그 보여줘" → 최근 로그
- "멈춰!" → Kill Switch

**복잡한 요청**:
- 분석, 설정 변경, 파라미터 튜닝
→ 개발 채팅(Gemini)에서 요청하세요

**장점**:
✅ 간단한 것: Telegram (외부 어디서나)
✅ 복잡한 것: 개발 채팅 (정확하고 안전)

**상호보완적!**"""
        
        self.send_message(msg)
        return "Help sent"
    
    def friendly_chat(self, message):
        """친근한 대화"""
        msg = f"""💬 안녕하세요!

"{message[:50]}..." 잘 받았습니다.

**간단한 명령 사용 가능**:
- "상태는?" - 시스템 확인
- "도움말" - 명령어 목록

**복잡한 작업**은 개발 채팅에서 하시면
더 정확하고 안전합니다! 🎯"""
        
        self.send_message(msg)
        return "Chat response sent"


# Global instance
_smart_handler = None

def get_smart_handler():
    global _smart_handler
    if _smart_handler is None:
        bot_token = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        _smart_handler = SmartTelegramHandler(bot_token, chat_id)
    return _smart_handler
