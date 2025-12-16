"""
Kiwoom Maintenance Watchdog
Monitors the health of Kiwoom Login UI and restarts it if necessary.
Handles common popups like 'Version Processing'.
Requirements: pywin32
"""

import sys
import time
import subprocess
import logging
import psutil
from pathlib import Path
from datetime import datetime, timedelta
import win32gui
import win32con
import win32process

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("g:/내 드라이브/garamdata/logs/kiwoom_watchdog.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CHECK_INTERVAL = 60  # Check every 60 seconds
HEARTBEAT_TIMEOUT = 300  # 5 minutes
SCRIPT_NAME = "kiwoom_login_ui.py"
PROJECT_ROOT = Path("c:/garam/garam")
START_SCRIPT = PROJECT_ROOT / "scripts" / SCRIPT_NAME
FLAG_PATH = PROJECT_ROOT / "GARAM_Data" / "kiwoom_ready.flag"

def find_kiwoom_process():
    """Find the running kiwoom_login_ui.py process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                # Check for python executing the script
                # Cmdline list usually: ['python', 'path/to/script.py']
                cmd_str = " ".join(cmdline).lower()
                if SCRIPT_NAME.lower() in cmd_str:
                    logger.info(f"Found Kiwoom process: PID={proc.pid}")
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def kill_process(proc):
    """Kill a process tree"""
    try:
        if proc.is_running():
            logger.info(f"Killing process {proc.pid}...")
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
    except Exception as e:
        logger.error(f"Failed to kill process: {e}")

def check_heartbeat():
    """Check if the connection flag is recent"""
    if not FLAG_PATH.exists():
        logger.warning(f"Heartbeat flag missing: {FLAG_PATH}")
        return False
        
    try:
        # Check file modification time
        mtime = datetime.fromtimestamp(FLAG_PATH.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        if age > HEARTBEAT_TIMEOUT:
            logger.warning(f"Heartbeat stale (Age: {age}s > {HEARTBEAT_TIMEOUT}s)")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking heartbeat: {e}")
        return False

def handle_popups():
    """Find and close/confirm known popups"""
    # Define handlers for window titles or class names
    # Kiwoom Version Processing
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        
        # Example 1: Version Processing (opversion)
        # Usually checking class '#32770' (Dialog) and specific title
        if "업그레이드" in title or "버전처리" in title:
            logger.info(f"Detected Popup: {title} ({class_name}) - Closing...")
            # Try to click 'OK' or 'Confirm'
            # Or just close it
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
        # Example 2: Confirm Dialogs
        if "확인" in title and class_name == "#32770":
             # This is risky, might close important dialogs, but for automation...
             # Better to be specific
             pass
             
    try:
        win32gui.EnumWindows(callback, None)
    except Exception as e:
        logger.error(f"Popup handler error: {e}")

def start_kiwoom():
    """Start the Kiwoom login script"""
    logger.info(f"Starting {SCRIPT_NAME}...")
    try:
        # Use specific 32-bit Python Path
        # Try to load from config, else fallback to the one we found
        python_exe = r"C:\Users\wanba\AppData\Local\Programs\Python\Python311-32\python.exe"
        
        # Check if exists
        if not Path(python_exe).exists():
             logger.error(f"32-bit Python not found at {python_exe}")
             return

        # Run in a new console -> REMOVED to prevent window clutter
        # It will inherit the watchdog's console or run in background
        subprocess.Popen(
            [python_exe, str(START_SCRIPT)],
            cwd=str(PROJECT_ROOT)
            # creationflags=subprocess.CREATE_NEW_CONSOLE # Commented out
        )
        logger.info(f"Process started using {python_exe}")
    except Exception as e:
        logger.error(f"Failed to start process: {e}")

def run_watchdog():
    """Main loop"""
    logger.info("Kiwoom Watchdog Started")
    
    while True:
        try:
            # 1. Check Stop Flag
            stop_flag = PROJECT_ROOT / "kiwoom_stop.flag"
            if stop_flag.exists():
                # If stopped by user, do nothing (maybe verify it's ded? check_heartbeat might be irrelevant)
                # Just ensure we don't restart it.
                # But we should still handle popups? Maybe not if not running.
                time.sleep(5)
                continue

            # 2. Handle Popups first
            handle_popups()
            
            # 2. Check Process
            proc = find_kiwoom_process()
            
            if proc:
                # Process is running, check heartbeat
                if check_heartbeat():
                    # All good
                    pass 
                else:
                    # Stale logic - DISABLED FOR STABILITY
                    # Just log it, do not kill. Let the UI handle itself or user manual intervene.
                    logger.warning("Process running but heartbeat stale. (Auto-kill disabled for stability)")
                    # kill_process(proc)
                    # time.sleep(5)
                    # start_kiwoom()
            else:
                # Process not running
                logger.warning("Kiwoom process not found. Starting...")
                start_kiwoom()
                
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Watchdog stopping...")
            break
        except Exception as e:
            logger.error(f"Watchdog Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_watchdog()
