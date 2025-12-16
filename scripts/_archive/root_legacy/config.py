"""
GARAM Path Configuration
Central configuration for all paths

사용법:
from garam.config import PATHS

PATHS.BASE_DIR  # C:/garam
PATHS.DATA_DIR  # C:/garam/GARAM_Data
etc.
"""

from pathlib import Path
import os
from enum import Enum

class ExecutionMode(Enum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"

class GaramPaths:
    """Central path configuration"""
    
    def __init__(self):
        # 환경 변수로 오버라이드 가능
        base_str = 'C:/garam/garam'
        self.BASE_DIR = Path(base_str)
        
        # Data Root - 장기 데이터 보관
        self.DATA_ROOT = Path("g:/내 드라이브/garamdata")
        
        # Core directories
        self.DATA_DIR = self.BASE_DIR / "GARAM_Data"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.REPLAY_PACK = self.BASE_DIR / "GARAM_AI_ReplayPack_v0_1"
        # self.AGENT_KIT = self.BASE_DIR / "AgentKit" # Removed
        self.UI_DIR = self.BASE_DIR / "GaramUI"
        
        # Config files
        self.CONFIG_DIR = self.BASE_DIR / "config"
        self.TRADING_MODE_FILE = self.CONFIG_DIR / "trading_mode.json"
        self.RISK_LIMITS_FILE = self.CONFIG_DIR / "risk_limits.json"
        
        # Scripts
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        
        # US Data Paths
        self.US_DATA_ROOT = self.DATA_DIR / "us"
        self.US_SP500_ROOT = self.US_DATA_ROOT / "sp500"
        
        # KR Data Paths
        self.KR_ROOT = self.DATA_DIR / "kr"
        
        # Google Drive Paths (Mirror)
        self.DRIVE_ROOT = self.DATA_ROOT
        self.DRIVE_US_ROOT = self.DRIVE_ROOT / "us"
        
        # Market data (임시/캐시)
        self.MARKET_DATA_DIR = self.DATA_DIR / "market_data"
        
        # Long-term data storage (garamdata)
        self.SYMBOLS_DIR = self.DATA_ROOT / "symbols"
        self.DAILY_DIR = self.DATA_ROOT / "daily"
        self.HISTORY_DIR = self.DATA_ROOT / "history"
        self.EXPERIMENTS_DIR = self.DATA_ROOT / "experiments"
        
        # Specific log directories
        self.SHADOW_LOGS = self.LOGS_DIR / "shadow"
        self.SIM_LOGS = self.LOGS_DIR / "simulation"
        self.OPTIM_LOGS = self.LOGS_DIR / "optim"
        self.PAPER_LOGS = self.LOGS_DIR / "paper"
        
        # [C-3] Centralized Data Paths
        self.HEALTH_DIR = self.DATA_DIR / "system"
        self.SIMULATION_DIR = self.DATA_DIR / "simulation"
        self.REPORTS_DIR = self.DATA_DIR / "reports"
        self.SHADOW_DIR = self.DATA_DIR / "shadow"
        self.GLOBAL_MODE_DIR = self.DATA_DIR / "global_mode"
        self.STRATEGY_DIR = self.DATA_DIR / "strategy"
        
        # Key Files
        self.KIWOOM_FLAG_PATH = self.DATA_DIR / "kiwoom_ready.flag"
        self.TODAY_SIM_FILE = self.REPORTS_DIR / "simulation_today.json"
        self.LATEST_HEALTH_FILE = self.HEALTH_DIR / "health_latest.json" # Alias if needed, or use glob
        
        # Strategy Files
        self.STRATEGY_DAILY_PLAN = self.STRATEGY_DIR / "daily_plan.json"
        self.STRATEGY_SIGNALS_LIVE = self.STRATEGY_DIR / "signals_live.json"
        self.STRATEGY_SIGNALS_HISTORY = self.STRATEGY_DIR / "signals_history.json"

        # [C-4] Live Operator View Data
        self.LIVE_DIR = self.DATA_DIR / "live"
        self.LIVE_TRADES = self.LIVE_DIR / "live_trades.csv"
        self.ACCOUNT_SNAPSHOT = self.LIVE_DIR / "account_snapshot.csv"
        self.CASH_EVENTS = self.LIVE_DIR / "cash_events.csv"
        self.DAILY_INTENT = self.LIVE_DIR / "daily_plan.json"

        # System Paths
        self.PYTHON_32 = Path(r"C:\Users\wanba\AppData\Local\Programs\Python\Python311-32\python.exe")
        
        # Create essential directories
        self._create_dirs()
    
    def _create_dirs(self):
        """Ensure essential directories exist"""
        for dir_path in [
            self.DATA_DIR,
            self.LOGS_DIR,
            self.CONFIG_DIR,
            self.MARKET_DATA_DIR,
            self.SHADOW_LOGS,
            self.SIM_LOGS,
            self.OPTIM_LOGS,
            self.PAPER_LOGS,
            # [C-3] New Dirs
            self.HEALTH_DIR,
            self.SIMULATION_DIR,
            self.REPORTS_DIR,
            self.SHADOW_DIR,
            self.GLOBAL_MODE_DIR,
            self.GLOBAL_MODE_DIR,
            self.STRATEGY_DIR,
            self.LIVE_DIR,
            # garamdata directories
            self.DATA_ROOT,
            self.SYMBOLS_DIR,
            self.DAILY_DIR,
            self.EXPERIMENTS_DIR,
            # US Data
            self.US_DATA_ROOT,
            self.US_SP500_ROOT
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        return f"GaramPaths(base={self.BASE_DIR})"

# Singleton instance
PATHS = GaramPaths()

# Legacy compatibility - 기존 코드와 호환
def get_base_path():
    """Legacy: Get base path"""
    return str(PATHS.BASE_DIR)

if __name__ == "__main__":
    print("GARAM Path Configuration")
    print("=" * 50)
    print(f"BASE_DIR: {PATHS.BASE_DIR}")
    print(f"DATA_DIR: {PATHS.DATA_DIR}")
    print(f"LOGS_DIR: {PATHS.LOGS_DIR}")
    print(f"CONFIG_DIR: {PATHS.CONFIG_DIR}")
    print(f"US_SP500_ROOT: {PATHS.US_SP500_ROOT}")
    print("=" * 50)
