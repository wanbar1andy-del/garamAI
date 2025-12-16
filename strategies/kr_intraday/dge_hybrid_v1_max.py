"""
DGE Hybrid V1 Max Profit
- Core: DGE Hybrid V1 (Regime Router + V2/V3)
- Modification: Risk per Trade = 2.0% (vs 1.0-1.5% standard)
- Goal: Maximize PnL using the proven Hybrid V1 engine.
"""

from strategies.kr_intraday.dge_hybrid_v1 import DGEHybridStrategyV1

class DGEHybridV1Max(DGEHybridStrategyV1):
    """
    DGE Hybrid V1 with Aggressive Sizing.
    """
    
    def __init__(self, account, config, daily_df=None, symbol="UNKNOWN"):
        # Force risk in config before init
        config['risk_per_trade'] = 0.02 # 2.0%
        super().__init__(account, config, daily_df, symbol)
        self.strategy_name = "DGE_Hybrid_v1_Max"
        
        # Double check
        self.risk_per_trade = 0.02
