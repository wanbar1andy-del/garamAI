
import pandas as pd
from pathlib import Path
import sys

# 프로젝트 루트 (c:\garam\garam)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.feature.feature_loader import features
from pipeline.signal.strategies import TurboStrategy
from pipeline.monitor.log_manager import LogManager

logger = LogManager.get_logger("SignalLoader")

class SignalLoader:
    """
    [Step 5: SIGNAL]
    Feature + Strategy -> Signal
    """
    def __init__(self):
        self.strategies = {
            'turbo': TurboStrategy(exit_threshold=0.03)
        }
    
    def get_signals(self, symbol, strategy_name='turbo'):
        """
        특정 전략에 따른 신호 생성
        """
        # 1. Feature Load (Store -> Feature)
        df = features.get_features(symbol)
        
        if df.empty:
            return df
        
        # 2. Strategy Execution
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            df_signal = strategy.generate_signals(df)
            return df_signal
        else:
            print(f"Unknown strategy: {strategy_name}")
            return df

signal_loader = SignalLoader()

if __name__ == "__main__":
    logger.info("=== SignalLoader Test ===")
    sample = "005930"
    df = signal_loader.get_signals(sample, 'turbo')
    
    if not df.empty:
        logger.info(f"Signal Generated for {sample}:")
        logger.info(f"\n{df[['date', 'close', 'day_open', 'daily_return', 'signal']].tail(10)}")
        
        # Panic Sell Test Check
        panic_sells = df[df['signal'] == -2]
        if not panic_sells.empty:
            logger.warning(f"Panic Sells Detected: {len(panic_sells)} times")
            logger.info(f"\n{panic_sells[['date', 'daily_return', 'signal']].head()}")
    else:
        logger.warning("No data.")
