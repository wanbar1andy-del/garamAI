"""
GARAM 시스템 자동 시작 마스터 스크립트
매일 아침 08:30 자동 실행
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('c:/garam/garam/logs/auto_start.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path('c:/garam/garam')
sys.path.insert(0, str(PROJECT_ROOT.parent))

from garam.config import PATHS

# Telegram Bot Integration - Simplified
def send_telegram(message, level='info'):
    """Send Telegram alert - direct API call"""
    try:
        bot_token = os.environ.get('GARAM_TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('GARAM_TELEGRAM_CHAT_ID')
        if not bot_token or not chat_id:
            return False
        
        emoji = {'info': '✅', 'warning': '⚠️', 'critical': '🚨'}
        text = f"{emoji.get(level, '📢')} *GARAM*\n\n{message}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

# Slack webhook (if configured) - Deprecated, use Telegram
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
                json={'text': f"{emoji.get(level, '📢')} GARAM: {message}"},
                timeout=5
            )
        except Exception as e:
            logger.warning(f"Failed to send alert: {e}")

def is_market_open_today():
    """Check if today is a market day"""
    today = datetime.now()
    # Monday=0, Sunday=6
    if today.weekday() >= 5:  # Weekend
        return False
    # TODO: Check holiday calendar
    return True

def pre_flight_check():
    """Pre-flight system check"""
    logger.info("🔍 Pre-flight check starting...")
    
    checks = []
    
    # Check 1: Python executable
    checks.append(('Python', sys.executable is not None))
    
    # Check 2: Essential files
    essential_files = [
        PROJECT_ROOT / 'api' / 'server_fixed.py',
        PROJECT_ROOT / 'scripts' / 'run_live_trading.py',
        PATHS.CONFIG_DIR / 'profile_champion_v3_weighted_400.yaml'
    ]
    
    for file_path in essential_files:
        checks.append((f'File: {file_path.name}', file_path.exists()))
    
    # Check 3: Data directory
    checks.append(('Data directory', PATHS.DATA_DIR.exists()))
    
    # Report
    all_passed = True
    for name, passed in checks:
        status = '✅' if passed else '❌'
        logger.info(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    return all_passed

def start_dashboard():
    """Start dashboard server"""
    logger.info("🚀 Starting dashboard server...")
    
    try:
        # Start in new console window
        subprocess.Popen(
            ['python', 'api/server_fixed.py'],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait and verify
        time.sleep(10)
        
        # Check if running
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Dashboard started successfully")
                return True
        except:
            pass
        
        logger.warning("⚠️ Dashboard may not be running correctly")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to start dashboard: {e}")
        return False

def start_kiwoom():
    """Start Kiwoom auto-connect"""
    if not is_market_open_today():
        logger.info("⏭️ Skipping Kiwoom (market closed)")
        return True
    
    logger.info("🔌 Starting Kiwoom connection...")
    
    try:
        # Check if 32-bit Python exists
        python_32 = Path(os.environ.get('GARAM_PYTHON_32', 
                         r'C:\Users\wanba\AppData\Local\Programs\Python\Python312-32\python.exe'))
        
        if not python_32.exists():
            logger.warning(f"⚠️ 32-bit Python not found: {python_32}")
            send_alert(f"Kiwoom 자동 연결 실패: 32-bit Python 미발견", 'warning')
            return False
        
        # Start Kiwoom login UI
        subprocess.Popen(
            [str(python_32), 'scripts/kiwoom_login_ui.py'],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        
        logger.info("✅ Kiwoom login UI launched")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start Kiwoom: {e}")
        send_alert(f"Kiwoom 자동 연결 실패: {e}", 'warning')
        return False

def start_live_trading():
    """Start live trading (optional, only if Kiwoom connected)"""
    if not is_market_open_today():
        logger.info("⏭️ Skipping live trading (market closed)")
        return True
    
    # Check if Kiwoom is connected
    if not PATHS.KIWOOM_FLAG_PATH.exists():
        logger.info("⏳ Waiting for Kiwoom connection before starting live trading")
        # Will be started by watchdog later
        return True
    
    logger.info("💹 Starting live trading...")
    
    try:
        subprocess.Popen(
            ['python', 'scripts/run_live_trading.py'],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("✅ Live trading started")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start live trading: {e}")
        send_alert(f"라이브 트레이딩 시작 실패: {e}", 'warning')
        return False

def verify_all_running():
    """Verify all critical services are running"""
    logger.info("🔍 Verifying services...")
    
    # Check dashboard
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        dashboard_ok = response.status_code == 200
    except:
        dashboard_ok = False
    
    logger.info(f"  {'✅' if dashboard_ok else '❌'} Dashboard")
    
    return dashboard_ok

def main():
    """Main auto-start sequence"""
    logger.info("=" * 70)
    logger.info("🚀 GARAM Auto-Start Initiated")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    send_alert(f"GARAM 자동 시작 시작", 'info')
    
    try:
        # Step 1: Pre-flight check
        if not pre_flight_check():
            logger.error("❌ Pre-flight check failed")
            send_alert("자동 시작 실패: Pre-flight check", 'critical')
            return 1
        
        # Step 2: Start Dashboard
        if not start_dashboard():
            logger.error("❌ Dashboard start failed")
            send_alert("자동 시작 실패: Dashboard", 'critical')
            return 1
        
        time.sleep(5)
        
        # Step 3: Start Kiwoom (if market day)
        start_kiwoom()
        
        time.sleep(10)
        
        # Step 4: Start Live Trading (if Kiwoom connected)
        # start_live_trading()  # Will be started by watchdog when ready
        
        # Step 5: Verify
        if verify_all_running():
            logger.info("✅ GARAM Auto-Start Complete")
            send_alert("✅ GARAM 자동 시작 완료", 'info')
            return 0
        else:
            logger.warning("⚠️ Some services may not be running")
            send_alert("⚠️ GARAM 일부 서비스 시작 실패", 'warning')
            return 1
            
    except Exception as e:
        logger.error(f"❌ Auto-start failed: {e}", exc_info=True)
        send_alert(f"자동 시작 실패: {e}", 'critical')
        return 1

if __name__ == "__main__":
    sys.exit(main())
