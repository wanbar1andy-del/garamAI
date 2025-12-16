"""
GARAM Telegram Minimal Listener
최소한의 코드로 확실하게 작동
"""

import os
import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN', '8284381258:AAENGcOgH6B6otI36C9L-AX1MrS_X-pPXRs')
CHAT_ID = os.environ.get('GARAM_TELEGRAM_CHAT_ID', '8362308273')
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram(message):
    """Telegram 메시지 전송"""
    try:
        url = f"{API_URL}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': message}
        r = requests.post(url, json=data, timeout=10)
        logger.info(f"Sent: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

def get_updates(offset=None):
    """업데이트 가져오기"""
    try:
        url = f"{API_URL}/getUpdates"
        params = {'timeout': 10}
        if offset:
            params['offset'] = offset
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get('result', [])
        return []
    except Exception as e:
        logger.error(f"Get updates error: {e}")
        return []

def understand_intent(text):
    """자연어 의도 파악 - 향상된 패턴 매칭"""
    msg = text.lower()
    
    # 상태 확인 패턴
    status_keywords = [
        '상태', 'status', '어때', '괜찮', '정상', '문제',
        '이상', '작동', '시스템', '대시보드', 'dashboard',
        '돌아가', '살아', '죽', '멈춤', '응답', '확인',
        '체크', 'check', '보고', '현황', 'ok'
    ]
    
    # 수익률 패턴
    return_keywords = [
        '수익', 'return', '성과', '얼마', '벌', '잃', 
        '돈', '자산', '퍼센트', '%', '손익', 'pnl',
        '이익', '손실', '투자', '총', '현금', '계좌'
    ]
    
    # 로그 패턴
    log_keywords = [
        '로그', 'log', '기록', '무슨', '뭐', '했',
        '이력', 'history', '활동', '내역'
    ]
    
    # Kill switch 패턴
    kill_keywords = [
        '멈춰', 'stop', '중단', 'kill', '정지', '끝',
        '그만', '다stop', '스톱', '꺼', 'halt'
    ]
    
    # 도움말 패턴
    help_keywords = [
        '도움', 'help', '명령', '가능', '할 수', 'command',
        '기능', '뭐해', '뭘할', '어떻게', 'how'
    ]
    
    # 패턴 매칭
    if any(kw in msg for kw in status_keywords):
        return 'status'
    elif any(kw in msg for kw in return_keywords):
        return 'return'
    elif any(kw in msg for kw in log_keywords):
        return 'log'
    elif any(kw in msg for kw in kill_keywords):
        return 'kill'
    elif any(kw in msg for kw in help_keywords):
        return 'help'
    else:
        return 'chat'

def ask_ai(user_message):
    """AI에게 자연어 질문 - OpenAI"""
    try:
        from openai import OpenAI
        
        api_key = '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'
        client = OpenAI(api_key=api_key)
        
        system_prompt = """당신은 GARAM 트레이딩 시스템의 AI 어시스턴트입니다.

사용자의 자연어 질문을 이해하고, 적절한 시스템 명령으로 변환하거나 직접 답변하세요.

**시스템 명령**:
- status: 시스템 상태 확인 (예: "괜찮아?", "시스템 어때?", "정상이야?")
- return: 수익률 조회 (예: "얼마 벌었어?", "돈은?", "수익은?")
- log: 로그 확인 (예: "로그 봐줘", "무슨 일 있었어?")
- kill: 긴급 중단 (예: "멈춰!", "중단해")
- help: 도움말 (예: "뭐할 수 있어?", "기능은?")

**응답 형식**:
{
  "intent": "status|return|log|kill|help|chat",
  "response": "사용자에게 보낼 메시지"
}

사용자가 일반 대화를 하면 intent를 'chat'으로 하고 친근하게 답변하세요."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse JSON response
        import json
        try:
            result = json.loads(ai_response)
            return result.get('intent', 'chat'), result.get('response', ai_response)
        except:
            # Fallback: treat as chat
            return 'chat', ai_response
            
    except Exception as e:
        logger.error(f"AI error: {e}")
        return None, None

def handle_message(text):
    """메시지 처리 - 자연어 이해"""
    # 1. Pattern matching first (빠름)
    intent = understand_intent(text)
    
    # 2. If chat intent, ask AI (자연어 이해)
    ai_intent = None
    ai_response = None
    
    if intent == 'chat':
        ai_intent, ai_response = ask_ai(text)
        if ai_intent:
            intent = ai_intent
    
    if intent == 'status':
        try:
            # Dashboard check
            try:
                r = requests.get('http://localhost:5000/health', timeout=3)
                dashboard = '✅ 정상' if r.status_code == 200 else '❌ 오류'
            except:
                dashboard = '❌ 미실행'
            
            # Kiwoom check
            import sys; sys.path.insert(0, 'c:/garam')
            from garam.config import PATHS
            kiwoom = '✅ 연결' if PATHS.KIWOOM_FLAG_PATH.exists() else '❌ 미연결'
            
            now = datetime.now().strftime('%H:%M:%S')
            send_telegram(f"📊 *GARAM 시스템*\n\nDashboard: {dashboard}\nKiwoom: {kiwoom}\n시각: {now}")
        except Exception as e:
            send_telegram(f"❌ 상태 확인 실패: {e}")
        return
    
    elif intent == 'return':
        try:
            import sys; sys.path.insert(0, 'c:/garam')
            from garam.config import PATHS
            import json
            
            # Read signals_live.json
            signal_file = PATHS.DATA_DIR / 'signals_live.json'
            if signal_file.exists():
                with open(signal_file, 'r') as f:
                    data = json.load(f)
                
                equity = data.get('total_equity', 0)
                cash = data.get('cash', 0)
                returns = ((equity - 10000000) / 10000000) * 100
                
                send_telegram(f"💰 *투자 성과*\n\n총 자산: {equity:,.0f}원\n현금: {cash:,.0f}원\n수익률: {returns:+.2f}%")
            else:
                send_telegram("📊 실시간 데이터 없음\n\n거래가 시작되면 확인 가능합니다.")
        except Exception as e:
            send_telegram(f"❌ 수익률 조회 실패: {e}")
        return
    
    # 로그
    if '로그' in msg or 'log' in msg:
        try:
            log_file = 'c:/garam/garam/logs/telegram_conversation.log'
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent = ''.join(lines[-15:])
            send_telegram(f"📝 *최근 로그*\n\n```\n{recent[:2000]}\n```")
        except Exception as e:
            send_telegram(f"❌ 로그 읽기 실패: {e}")
        return
    
    # Kill
    if '멈춰' in msg or 'kill' in msg or '중단' in msg:
        send_telegram("🚨 *Kill Switch*\n\n⚠️ 긴급 중단 요청됨\n\n실제 중단은 여기(개발 채팅)에서 확인 후 실행하세요!")
        return
    
    elif intent == 'help':
        send_telegram("📚 *명령어*\n\n- 상태 → 시스템 확인\n- 수익률 → 투자 성과\n- 로그 → 최근 로그\n- 멈춰 → Kill Switch\n- 도움말 → 이 메시지\n\n**자연어도 가능!**\n\"시스템 어때?\", \"얼마 벌었어?\" 등")
        return
    
    elif intent == 'chat':
        # AI conversation
        if ai_response:
            send_telegram(f"🤖 {ai_response}")
        else:
            send_telegram(f"✅ 메시지 받음\n\n'{text[:50]}...'\n\n자연어로 편하게 물어보세요!")
        return
    
    # 기본 응답
    send_telegram(f"✅ '{text[:50]}...'\n\n명령: 상태/수익률/로그/도움말")

def main():
    logger.info("🚀 Minimal Listener 시작")
    send_telegram("🤖 Minimal Listener 시작!\n\n명령어:\n- 상태\n- 로그\n- 멈춰\n- 도움말")
    
    last_update_id = 0
    
    logger.info("👂 대기 중...")
    
    try:
        while True:
            updates = get_updates(offset=last_update_id + 1)
            
            for update in updates:
                update_id = update.get('update_id', 0)
                if update_id > last_update_id:
                    last_update_id = update_id
                
                if 'message' in update:
                    message = update['message']
                    text = message.get('text', '')
                    user = message.get('from', {}).get('first_name', 'User')
                    
                    logger.info(f"📨 '{text}' from {user}")
                    
                    if text.startswith('/'):
                        # 명령어
                        if '/status' in text:
                            send_telegram("📊 시스템 정상")
                        elif '/help' in text:
                            send_telegram("📚 도움말\n\n명령: 상태/로그")
                    else:
                        # 자연어
                        handle_message(text)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("⏹️ 중지")
        send_telegram("🛑 Listener 중지됨")

if __name__ == "__main__":
    main()
