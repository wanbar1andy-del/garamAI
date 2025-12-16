"""
GARAM Telegram Bot
양방향 통신: 알림 송신 + 명령 수신
"""

import os
import sys
import logging
import requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GaramTelegramBot:
    """
    GARAM Telegram Bot Manager
    
    기능:
    1. 알림 송신 (Info, Warning, Critical)
    2. 명령 수신 (Kill Switch, Status, Restart, Approve)
    3. 승인 요청/응답
    """
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured. Set GARAM_TELEGRAM_BOT_TOKEN and GARAM_TELEGRAM_CHAT_ID")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram bot enabled (Chat ID: {self.chat_id})")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Approval tracking
        self.pending_approvals = {}
    
    def send_message(self, message, level='info', parse_mode='Markdown'):
        """
        텔레그램 메시지 송신
        
        Args:
            message: 메시지 내용
            level: 'info', 'warning', 'critical'
            parse_mode: 'Markdown' or 'HTML'
        """
        if not self.enabled:
            logger.debug(f"Telegram disabled: {message}")
            return False
        
        # 레벨별 이모지
        emoji_map = {
            'info': '✅',
            'warning': '⚠️',
            'critical': '🚨',
            'success': '✅',
            'error': '❌',
            'debug': '🔍'
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
            
            if response.status_code == 200:
                logger.info(f"Telegram sent: {level}")
                return True
            else:
                logger.error(f"Telegram failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def send_alert(self, message, level='info'):
        """Alias for send_message"""
        return self.send_message(message, level)
    
    def send_keyboard(self, message, buttons):
        """
        인라인 키보드와 함께 메시지 송신
        
        Args:
            message: 메시지
            buttons: [[{'text': 'Button', 'callback_data': 'data'}]]
        """
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
            logger.error(f"Keyboard send error: {e}")
            return False
    
    def request_approval(self, action, reason, timeout=300):
        """
        승인 요청
        
        Args:
            action: 실행할 액션 (예: 'stop_trading')
            reason: 승인 사유
            timeout: 자동 거부 시간 (초)
        
        Returns:
            approval_id: 승인 요청 ID
        """
        approval_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        message = f"""
🚨 *승인 필요*

**액션**: `{action}`
**사유**: {reason}
**Timeout**: {timeout//60}분

승인 또는 거부하세요.
        """
        
        buttons = [
            [
                {'text': '✅ 승인', 'callback_data': f'approve_{approval_id}'},
                {'text': '❌ 거부', 'callback_data': f'reject_{approval_id}'}
            ]
        ]
        
        self.pending_approvals[approval_id] = {
            'action': action,
            'reason': reason,
            'status': 'pending',
            'sent_at': datetime.now()
        }
        
        self.send_keyboard(message, buttons)
        
        return approval_id
    
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
        명령 처리
        
        Commands:
        /status - 시스템 상태
        /kill - 긴급 중단
        /restart - 재시작
        /approve - 승인
        /reject - 거부
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
            return f"알 수 없는 명령: {command}\n/help 로 도움말 확인"
    
    def cmd_status(self):
        """시스템 상태 조회"""
        try:
            # Check dashboard
            import requests as req
            try:
                resp = req.get('http://localhost:5000/health', timeout=3)
                dashboard = '✅ Running' if resp.status_code == 200 else '❌ Down'
            except:
                dashboard = '❌ Down'
            
            # Check Kiwoom
            sys.path.insert(0, 'c:/garam')
            from garam.config import PATHS
            kiwoom = '✅ Connected' if PATHS.KIWOOM_FLAG_PATH.exists() else '❌ Disconnected'
            
            status = f"""
📊 *GARAM 시스템 상태*

**Dashboard**: {dashboard}
**Kiwoom**: {kiwoom}
**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_message(status, 'info')
            return "Status sent"
            
        except Exception as e:
            return f"Status check failed: {e}"
    
    def cmd_kill_switch(self):
        """긴급 중단 (Kill Switch)"""
        self.send_message("🚨 *Kill Switch 활성화*\n\n모든 거래 중단 중...", 'critical')
        
        # TODO: 실제 중단 로직 구현
        # stop_all_trading()
        # close_all_positions()
        
        return "Kill switch activated"
    
    def cmd_restart(self):
        """시스템 재시작"""
        self.send_message("🔄 *시스템 재시작*\n\nDashboard 재시작 중...", 'warning')
        
        # TODO: 실제 재시작 로직
        # restart_dashboard()
        
        return "Restart initiated"
    
    def cmd_help(self):
        """도움말"""
        help_text = """
📚 *GARAM Bot 명령어*

`/status` - 시스템 상태 확인
`/kill` - ⚠️ 긴급 거래 중단
`/restart` - Dashboard 재시작
`/help` - 이 도움말

**승인 요청**
버튼을 눌러 승인/거부
        """
        
        self.send_message(help_text, 'info')
        return "Help sent"


# Global instance
_telegram_bot = None

def get_telegram_bot():
    """Get global Telegram bot instance"""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = GaramTelegramBot()
    return _telegram_bot


def send_telegram(message, level='info'):
    """Convenience function to send Telegram message"""
    bot = get_telegram_bot()
    return bot.send_alert(message, level)


if __name__ == "__main__":
    # Test
    bot = GaramTelegramBot()
    
    if bot.enabled:
        print("Testing Telegram bot...")
        
        # Test 1: Simple message
        bot.send_alert("🚀 GARAM Bot Test", 'info')
        
        # Test 2: Status
        bot.cmd_status()
        
        print("✅ Test messages sent!")
    else:
        print("❌ Telegram bot not configured")
        print("Set environment variables:")
        print("  GARAM_TELEGRAM_BOT_TOKEN")
        print("  GARAM_TELEGRAM_CHAT_ID")
