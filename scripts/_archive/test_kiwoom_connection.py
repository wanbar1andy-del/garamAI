from pykiwoom.kiwoom import Kiwoom
import sys
import logging
import time

# Setup logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_connect():
    try:
        logger.info("Initializing Kiwoom Object...")
        kiwoom = Kiwoom()
        
        logger.info("Attempting CommConnect (Check if logged in)...")
        # CommConnect usually triggers the login window if not logged in.
        # If already logged in via another process or OCX state, it might succeed.
        kiwoom.CommConnect(block=True)
        
        state = kiwoom.GetConnectState()
        if state == 1:
            logger.info(">>> Kiwoom Connection State: CONNECTED (1)")
            
            # Try a simple query
            user_id = kiwoom.GetLoginInfo("USER_ID")
            user_name = kiwoom.GetLoginInfo("USER_NAME")
            server_type = kiwoom.GetLoginInfo("GetServerGubun") # 1: Mock, others: Real
            
            logger.info(f"User ID: {user_id}")
            logger.info(f"User Name: {user_name}")
            logger.info(f"Server Type: {'Mock' if server_type == '1' else 'Real'}")
            
        elif state == 0:
            logger.error(">>> Kiwoom Connection State: DISCONNECTED (0)")
        else:
            logger.warning(f">>> Kiwoom Connection State: Unknown ({state})")
            
    except Exception as e:
        logger.error(f"CRITICAL ERROR during connection test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connect()
