"""
GARAM Telegram Bot with Natural Language Processing (2-Lane Ops)
Lane A: Execution (Strict Approval) - status, kill, restart
Lane B: Query (Auto Report) - report, query, holdings, hero, etc.
"""

import os
import sys
import logging
import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GaramTelegramBotV2:
    def __init__(self, bot_token=None, chat_id=None, gemini_api_key=None):
        self.bot_token = bot_token or os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY')
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram bot enabled with Gemini AI")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.pending_approvals = {}  # chat_id -> {intent, prompt, ts}
        
        # System Prompt (Expanded)
        self.system_prompt = """당신은 가람(GARAM) 시스템의 AI 운영 비서입니다.
사용자의 질문/명령을 분석하여 다음 JSON으로 응답합니다.

[Intent Categories]
1. Lane A (실행/제어):
   - status: "상태 어때?", "보고" (단순 상태확인)
   - restart: "재시작", "다시 켜", "리셋" (승인필수)
   - kill: "멈춰", "중단", "꺼라", "청산" (승인필수)
   
2. Lane B (조회/리포트):
   - report: "리포트 줘", "요약해줘", "브리핑" (종합 보고)
   - query: "히어로 뭐야?", "현금 얼마?", "보유 종목?", "1주일 그래프" (특정 정보 조회)
   - chat: 시스템과 무관한 농담/인사 ("안녕", "심심해")

[Response Format]
{
  "intent": "status|restart|kill|report|query|chat",
  "confidence": 0.0-1.0,
  "needs_confirmation": boolean,
  "response": "사용자에게 보여줄 한국어 메시지 (실행 전 확인용 또는 즉답)"
}

[Rules]
- 'restart', 'kill'은 반드시 needs_confirmation: true
- 모호한 질문(예: "잘 돌아가?", "얼마 벌었어?")은 'report' 또는 'query'로 분류하여 자동 리포팅 유도.
- 'chat'은 정말 운영과 무관한 경우만.
"""
    
    def _is_authorized(self, update: dict) -> bool:
        try:
            if "message" in update:
                chat_id = str(update["message"]["chat"]["id"])
            elif "callback_query" in update:
                chat_id = str(update["callback_query"]["message"]["chat"]["id"])
            else:
                return False

            if str(self.chat_id) != chat_id:
                return False
            return True
        except Exception:
            return False

    def _set_pending(self, intent: str, prompt: str):
        self.pending_approvals[str(self.chat_id)] = {
            "intent": intent,
            "prompt": prompt,
            "ts": datetime.utcnow().isoformat()
        }

    def _pop_pending(self):
        return self.pending_approvals.pop(str(self.chat_id), None)

    def _extract_first_json(self, text: str):
        """
        Extract first JSON object from text using regex to handle markdown fences or trailing text.
        """
        try:
            # Look for outermost { ... }
            m = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not m:
                # If regex fails, try plain json loads on stripped text
                return json.loads(text.strip())
            return json.loads(m.group(0))
        except Exception:
            raise ValueError("No JSON found")

    def send_message(self, message, level='info', parse_mode=None):
        if not self.enabled: return False
        emoji_map = {'info': '📢', 'warning': '⚠️', 'critical': '🚨', 'success': '✅', 'error': '❌'}
        emoji = emoji_map.get(level, '📢')
        formatted_message = f"{emoji} [가람 봇] {message}"
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {'chat_id': self.chat_id, 'text': formatted_message}
            if parse_mode: payload['parse_mode'] = parse_mode
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    
    def send_keyboard(self, message, buttons):
        if not self.enabled: return False
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id, 
                'text': message, 
                'reply_markup': {'inline_keyboard': buttons}
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Keyboard error: {e}")
    
    def get_updates(self, offset=None):
        if not self.enabled: return []
        try:
            url = f"{self.api_url}/getUpdates"
            params = {'timeout': 30}
            if offset: params['offset'] = offset
            response = requests.get(url, params=params, timeout=40)
            if response.status_code == 200:
                return response.json().get('result', [])
        except Exception as e:
            logger.error(f"Get updates error: {e}")
            time.sleep(5)
        return []
    
    def run_polling(self):
        if not self.enabled:
            logger.error("Bot not enabled")
            return

        logger.info("🤖 가람 봇(2-Lane Ops) 시작됨...")
        self.send_message("🤖 **가람 2.0 봇**이 온라인 상태입니다.\n명령 또는 질문을 자유롭게 하세요!", 'success', parse_mode='Markdown')
        
        offset = None
        while True:
            updates = self.get_updates(offset)
            for update in updates:
                offset = update['update_id'] + 1
                
                if not self._is_authorized(update):
                    continue

                if 'message' in update and 'text' in update['message']:
                    text = update['message']['text']
                    self.handle_natural_message(text)
                
                if 'callback_query' in update:
                    callback = update['callback_query']
                    callback_id = callback['id']
                    data = callback['data']
                    try:
                        requests.post(f"{self.api_url}/answerCallbackQuery", json={'callback_query_id': callback_id})
                    except:
                        pass
                    self.handle_callback(data)

    def handle_callback(self, data):
        if data.startswith('confirm_'):
            intent = data.replace('confirm_', '')
            self._pop_pending()
            self.send_message(f"✅ 승인됨: {intent} 실행합니다.", 'success')
            self.execute_command(intent)
        elif data == 'cancel':
            self._pop_pending()
            self.send_message("❌ 취소되었습니다.", 'info')

    def parse_natural_language(self, user_message):
        if not self.gemini_api_key:
            return self.fallback_parser(user_message)
        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": f"{self.system_prompt}\n\n사용자: {user_message}"}]}],
                "generationConfig": {"temperature": 0.3}
            }
            response = requests.post(f"{url}?key={self.gemini_api_key}", headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                content = response.json()['candidates'][0]['content']['parts'][0]['text']
                # Clean fences
                content = content.replace('```json', '').replace('```', '').strip()
                # Robust extraction
                return self._extract_first_json(content)
            return self.fallback_parser(user_message)
        except Exception as e:
            logger.error(f"NLP Error: {e}")
            return self.fallback_parser(user_message)
    
    def fallback_parser(self, user_message):
        msg = user_message.lower()
        if any(kw in msg for kw in ['멈춰', '중단', 'kill', 'stop']):
            return {'intent': 'kill', 'confidence': 1.0, 'needs_confirmation': True, 'response': '⚠️ 비상 정지를 수행할까요?'}
        if any(kw in msg for kw in ['재시작', 'restart']):
            return {'intent': 'restart', 'confidence': 1.0, 'needs_confirmation': True, 'response': '재시작할까요?'}
        # Default fallback is now REPORT (Auto-Lane)
        return {'intent': 'report', 'confidence': 0.8, 'needs_confirmation': False, 'response': '리포트를 생성합니다.'}

    def handle_natural_message(self, user_message):
        msg = (user_message or "").strip()
        
        # 1. Text Approval
        if msg in ["승인", "확인", "ok", "OK", "ㅇㅋ"]:
            pending = self._pop_pending()
            if not pending:
                self.send_message("승인 대기 중인 작업이 없습니다.", "info")
                return
            intent = pending["intent"]
            self.send_message(f"✅ 승인됨: {intent} 실행.", "success")
            self.execute_command(intent)
            return

        if msg in ["취소", "cancel", "CANCEL", "ㄴㄴ"]:
            pending = self._pop_pending()
            if pending:
                self.send_message("❌ 취소되었습니다.", "info")
            else:
                self.send_message("취소할 작업이 없습니다.", "info")
            return

        # Fast-path: Operational Readiness Report (GO/NO-GO)
        if re.search(r"(3\s*개월|90\s*일|적합성|readiness|go.*no.*go|운영.*리포트|turbo|터보|1억)", msg, flags=re.IGNORECASE):
            self.send_message("🔍 [운영 적합성 판정] 최근 3개월 데이터 기반 GO/NO-GO 리포트를 생성합니다...", "info")
            self.execute_command("turbo3m")
            return
            
        # Fast-path: Hero 10% Reach Analysis
        if re.search(r"(히어로.*10|10\s*퍼|10\s*%|hero.*10|시장.*기회|reach)", msg, flags=re.IGNORECASE):
            self.send_message("🚀 [Hero 10% Reach] 히어로 선정 후 10% 도달 확률을 분석합니다...", "info")
            self.execute_command("hero10")
            return

        # Fast-path: Hero 70% Capture Analysis
        if re.search(r"(히어로.*70|70\s*캡처|5일\s*히어로|hero.*capture|캡처율)", msg, flags=re.IGNORECASE):
            self.send_message("🧪 [Hero 70% Capture] 5일 보유 시 70% 캡처 검증을 시작합니다...\n(약 1분 소요)", "info")
            self.execute_command("measure_70")
            return
            
        # 2. NLP Routing
        result = self.parse_natural_language(msg)
        intent = result.get('intent', 'report') # Default to report if unsure
        confirm = result.get('needs_confirmation', False)
        resp = result.get('response', '')
        
        # [CRITICAL] 2. Force Confirmation Safety Override
        if intent in ['kill', 'restart']:
            confirm = True
            result['needs_confirmation'] = True

        # Lane B: Query/Report -> Auto Execute (No Approval)
        if intent in ['report', 'query', 'status'] and not confirm:
            self.send_message(f"🔎 {resp} (조회중...)", 'info')
            self.execute_command('snapshot') # Always give full snapshot with graph
            return

        # Lane A: Execution -> Approval Required
        if confirm:
            self._set_pending(intent, resp)
            buttons = [[
                {'text': '✅ 승인 (실행)', 'callback_data': f'confirm_{intent}'},
                {'text': '❌ 취소', 'callback_data': 'cancel'}
            ]]
            self.send_keyboard(f"⚠️ **승인 요청**\n\n{resp}\n\n'승인' 또는 '취소' 입력 가능 (텍스트/버튼)", buttons)
            return
            
        # Common Chat
        if intent == 'chat':
             self.send_message(resp, 'info')
             return

        # Fallback
        self.send_message(f"알 수 없는 요청입니다. 리포트를 보여드릴까요?", 'warning')

    def execute_command(self, intent):
        import subprocess
        try:
            if intent in ['status', 'report', 'query', 'snapshot']:
                # Call telegram_ops_report.py with snapshot mode (includes graph)
                cmd = ["C:\\Python313\\python.exe", "C:\\garam\\garam\\scripts\\ops\\telegram_ops_report.py", "snapshot"]
                subprocess.Popen(cmd)
                
            elif intent == 'turbo3m':
                # New: Operational Readiness Report (GO/NO-GO)
                cmd = ["C:\\Python313\\python.exe", "C:\\garam\\garam\\scripts\\ops\\generate_ops_readiness_report.py"]
                subprocess.Popen(cmd)
                
            elif intent == 'hero10':
                # Hero 10% Reach Analysis
                cmd = ["C:\\Python313\\python.exe", "C:\\garam\\garam\\scripts\\ops\\analyze_hero_10pct_reach.py"]
                subprocess.Popen(cmd)
                
            elif intent == 'measure_70':
                # Hero 70% Capture Analysis
                cmd = ["C:\\Python313\\python.exe", "C:\\garam\\garam\\scripts\\ops\\analyze_hero_capture70_5d.py"]
                subprocess.Popen(cmd)
                
            elif intent == 'restart':
                self.send_message("🔄 Ingester 재시작 스크립트 실행...", 'warning')
                cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\garam\\garam\\scripts\\ops\\restart_ingester.ps1"]
                subprocess.Popen(cmd)
                
            elif intent == 'kill':
                self.send_message("🚨 모든 프로세스 종료(Auto Logout)...", 'critical')
                cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\garam\\garam\\scripts\\ops\\auto_logout.ps1"]
                subprocess.Popen(cmd)
                
        except Exception as e:
            self.send_message(f"실행 실패: {e}", 'error')

if __name__ == "__main__":
    bot = GaramTelegramBotV2()
    if bot.enabled:
        try:
            bot.run_polling()
        except KeyboardInterrupt:
            pass
    else:
        print("Bot init failed")
