import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from garam.utils.telegram_bot_v2 import GaramTelegramBotV2
from garam.utils.telegram_smart_handler import SmartTelegramHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_complex_request(message):
    """
    복잡한 요청(AI 처리 필요) 감지
    """
    msg = message.lower()
    
    # AI 처리가 필요한 키워드
    ai_keywords = [
        # 분석 요청
        '분석', 'analyze', '왜', '원인', 'why', '이유',
        # 변경 요청
        '변경', '튜닝', '최적화', 'tune', 'optimize', 'change',
        # 리포트 요청
        '리포트', '보고서', '요약', 'report', 'summary',
        # 진단 요청
        '진단', '문제', '오류', 'diagnose', 'problem', 'error',
        # 로그 요청
        '로그', 'log', '기록', '히스토리',
        # 백테스트
        '백테스트', 'backtest', '시뮬레이션',
        # 설정
        '설정', 'config', '파라미터', 'parameter'
    ]
    
    # 복잡한 요청 감지
    if any(keyword in msg for keyword in ai_keywords):
        return True
    
    # 질문 형태 ("어떻게", "무엇을", "언제" 등)
    question_words = ['어떻게', '무엇', '언제', '어디', 'how', 'what', 'when', 'where']
    if any(word in msg for word in question_words):
        return True
    
    return False

def main():
    """
    Telegram 명령 리스너 메인 루프
    """
    logger.info("🤖 GARAM Telegram Listener 시작")
    
    # Initialize bot and Smart Handler
    bot = GaramTelegramBotV2()
    smart_handler = SmartTelegramHandler(
        bot_token=os.environ.get('GARAM_TELEGRAM_BOT_TOKEN'),
        chat_id=os.environ.get('GARAM_TELEGRAM_CHAT_ID')
    )
    
    if not bot.enabled:
        logger.error("❌ Telegram bot not configured")
        logger.error("Set environment variables:")
        logger.error("  GARAM_TELEGRAM_BOT_TOKEN")
        logger.error("  GARAM_TELEGRAM_CHAT_ID")
        return 1
    
    logger.info(f"✅ Bot enabled (Chat ID: {bot.chat_id})")
    logger.info(f"✅ Smart Handler enabled (No Gemini API)")
    smart_handler.send_message("🤖 *Smart Handler 시작!*\n\n간단한 명령을 자유롭게 사용하세요.\n복잡한 작업은 개발 채팅에서!")
    
    # Conversation log file
    log_file = Path('c:/garam/garam/logs/telegram_conversation.log')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_conversation(user_msg, bot_response, intent='unknown'):
        """대화 로그 기록"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}]\n")
            f.write(f"사용자: {user_msg}\n")
            f.write(f"Intent: {intent}\n")
            f.write(f"봇 응답: {bot_response}\n")
    
    # Track last update
    last_update_id = 0
    
    logger.info("👂 명령 대기 중...")
    logger.info(f"📝 대화 로그: {log_file}")
    
    try:
        while True:
            # Get updates
            updates = bot.get_updates(offset=last_update_id + 1)
            
            for update in updates:
                # Update offset
                update_id = update.get('update_id', 0)
                if update_id > last_update_id:
                    last_update_id = update_id
                
                # Handle message
                if 'message' in update:
                    message = update['message']
                    text = message.get('text', '')
                    user = message.get('from', {})
                    user_name = user.get('first_name', 'User')
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"📨 사용자 메시지: '{text}'")
                    logger.info(f"   보낸 사람: {user_name}")
                    
                    # Route to appropriate handler
                    if text.startswith('/'):
                        # Traditional command
                        command = text.split()[0]
                        logger.info(f"   타입: 전통 명령어")
                        bot.handle_command(command)
                        log_conversation(text, f"명령 실행: {command}", command)
                    
                    else:
                        # All natural language → Smart Handler
                        logger.info(f"   타입: 🎯 Smart Handler")
                        
                        # Smart Handler에게 전달
                        smart_handler.handle_message(text)
                        log_conversation(text, f"Smart처리: {text[:30]}...", "smart_handler")
                
                # Handle callback (button clicks)
                elif 'callback_query' in update:
                    callback = update['callback_query']
                    data = callback.get('data', '')
                    
                    logger.info(f"🔘 버튼 클릭: {data}")
                    
                    if data.startswith('confirm_'):
                        intent = data.replace('confirm_', '')
                        bot.send_message(f"✅ '{intent}' 실행!", 'success')
                        bot.execute_command(intent)
                        log_conversation(f"[버튼] {data}", f"실행: {intent}", intent)
                    elif data == 'cancel':
                        bot.send_message("❌ 취소되었습니다.", 'info')
                        log_conversation(f"[버튼] {data}", "취소됨", "cancel")
            
            # Sleep
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Listener 중지")
        bot.send_message("🛑 Bot 리스너 중지됨", 'info')
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        bot.send_message(f"❌ 오류 발생: {e}", 'error')
        return 1

if __name__ == "__main__":
    sys.exit(main())
