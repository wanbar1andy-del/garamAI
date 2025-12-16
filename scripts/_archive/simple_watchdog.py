"""
GARAM Simple Watchdog
프로세스 감시 및 자동 재시작
"""

import os
import sys
import time
import subprocess
import logging
import requests
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('c:/garam/garam/logs/watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path('c:/garam/garam')
sys.path.insert(0, str(PROJECT_ROOT.parent))

from garam.config import PATHS

# Telegram Integration - Simplified
def send_telegram(message, level='info'):
    """Send Telegram alert - direct API call"""
    try:
        bot_token = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        if not bot_token or not chat_id:
            return False
        
        emoji = {'info': '✅', 'warning': '⚠️', 'critical': '🚨'}
        text = f"{emoji.get(level, '🔧')} *Watchdog*\n\n{message}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

SLACK_WEBHOOK = os.environ.get('GARAM_SLACK_WEBHOOK', '')

def send_alert(message, level='info'):
    """Send alert via Telegram (primary) or Slack (fallback)"""
    # Try Telegram first
    if send_telegram(message, level):
        return
    
    # Fallback to Slack
    if SLACK_WEBHOOK:
        try:
            emoji = {'info': '✅', 'warning': '⚠️', 'critical': '🚨'}
            requests.post(
                SLACK_WEBHOOK,
                json={'text': f"{emoji.get(level, '🔧')} Watchdog: {message}"},
                timeout=5
            )
        except:
            pass

def is_dashboard_running():
    """Check if dashboard server is running"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=3)
        return response.status_code == 200
    except:
        return False

def restart_dashboard():
    """Restart dashboard server"""
    logger.warning("🔧 Restarting dashboard...")
    send_alert("Dashboard 다운 감지, 재시작 중...", 'warning')
    
    try:
        subprocess.Popen(
            ['python', 'api/server_fixed.py'],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for restart
        time.sleep(10)
        
        if is_dashboard_running():
            logger.info("✅ Dashboard restarted successfully")
            send_alert("Dashboard 재시작 성공", 'info')
            return True
        else:
            logger.error("❌ Dashboard restart failed")
            send_alert("Dashboard 재시작 실패", 'critical')
            return False
            
    except Exception as e:
        logger.error(f"❌ Dashboard restart error: {e}")
        send_alert(f"Dashboard 재시작 오류: {e}", 'critical')
        return False

def is_kiwoom_connected():
    """Check if Kiwoom is connected"""
    return PATHS.KIWOOM_FLAG_PATH.exists()

def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        total, used, free = shutil.disk_usage('c:/')
        free_gb = free // (2**30)
        
        if free_gb < 10:
            logger.warning(f"⚠️ Low disk space: {free_gb}GB")
            send_alert(f"디스크 여유공간 부족: {free_gb}GB", 'warning')
            # Auto cleanup logs
            cleanup_old_logs()
        
        return free_gb > 5
    except:
        return True

def cleanup_old_logs():
    """Cleanup old log files"""
    logger.info("🧹 Cleaning up old logs...")
    
    try:
        log_dir = PATHS.LOGS_DIR
        if log_dir.exists():
            import glob
            from datetime import timedelta
            
            # Delete logs older than 30 days
            cutoff = datetime.now() - timedelta(days=30)
            
            for log_file in log_dir.glob('*.log'):
                if log_file.stat().st_mtime < cutoff.timestamp():
                    log_file.unlink()
                    logger.info(f"  Deleted: {log_file.name}")
            
            logger.info("✅ Log cleanup complete")
            send_alert("오래된 로그 파일 정리 완료", 'info')
    except Exception as e:
        logger.warning(f"Log cleanup failed: {e}")

def main():
    """Main watchdog loop"""
    logger.info("=" * 70)
    logger.info("🔧 GARAM Watchdog Started")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    send_alert("Watchdog 시작", 'info')
    
    restart_count = 0
    max_restarts = 5
    
    while True:
        try:
            # Check 1: Dashboard running
            if not is_dashboard_running():
                logger.warning("❌ Dashboard is not running")
                
                if restart_count < max_restarts:
                    restart_dashboard()
                    restart_count += 1
                else:
                    logger.error(f"🚨 Max restart attempts ({max_restarts}) reached")
                    send_alert(f"Dashboard 재시작 {max_restarts}회 실패, 수동 개입 필요", 'critical')
                    # Wait longer before trying again
                    time.sleep(300)
                    restart_count = 0
            else:
                # Dashboard is healthy, reset counter
                if restart_count > 0:
                    restart_count = 0
                    logger.info("✅ Dashboard healthy")
            
            # Check 2: Kiwoom status (just log)
            kiwoom_status = "Connected" if is_kiwoom_connected() else "Disconnected"
            logger.debug(f"Kiwoom: {kiwoom_status}")
            
            # Check 3: Disk space
            check_disk_space()
            
            # Sleep
            time.sleep(60)  # Check every 1 minute
            
        except KeyboardInterrupt:
            logger.info("🛑 Watchdog stopped by user")
            send_alert("Watchdog 중지됨", 'info')
            break
            
        except Exception as e:
            logger.error(f"Watchdog error: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()
