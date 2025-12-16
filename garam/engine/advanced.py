from typing import Dict, Any
import pandas as pd
from .base import BaseEngine
from .components.hmm_detector import HMMRegimeDetector
from .components.macro_analyzer import MacroFactorAnalyzer

class AdvancedEngine(BaseEngine):
    """
    Engine 2: The new Market Sensing System.
    Focus: HMM Regime Detection, Macro Factors.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("engine2", config)
        self.regime = "UNKNOWN"
        
        # Initialize Components
        self.hmm = HMMRegimeDetector()
        self.macro = MacroFactorAnalyzer()
        
        # Try to train HMM on startup if history is available
        # In production, this should be done offline or cached
        self._initialize_hmm_if_possible()

    def _initialize_hmm_if_possible(self):
        """Attempt to load KOSPI history to train HMM"""
        try:
            # Assumes standard path from GARAM structure
            path = "C:/garam/garam/GARAM_Data/history/labeled_KR_KOSPI_daily_20y.csv"
            df = pd.read_csv(path)
            if 'close' in df.columns:
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                # Train on last 2000 days (~8 years)
                self.hmm.train(df['close'].tail(2000))
                self.regime = self.hmm.predict_regime(df['close'].tail(50))
        except Exception as e:
            print(f"[AdvancedEngine] HMM Init Warning: {e}")

    def generate_signals(self, market_data: Any) -> Dict[str, float]:
        """
        Generates signals based on specific quantitative models.
        """
        signals = {}
        
        # 1. Update Regime
        # In live mode, we would append new data point to HMM
        # self.regime = self.hmm.predict_regime(current_price_series)
        
        # 2. Macro Check
        macro_status = self.macro.analyze()
        
        # 3. Generate Score
        # Simple Logic: If Bull Regime, Buy All (Score 1.0)
        # If Bear Regime, Sell All (Score -1.0)
        # If Sideways, Neutral (Score 0.0)
        
        base_score = 0.0
        if self.regime == "BULL":
            base_score = 1.0
        elif self.regime == "BEAR":
            base_score = -1.0
        
        # Filter by Macro
        if macro_status.get("exchange_rate") == "BEAR":
            base_score -= 0.5 # Reduce conviction
            
        # Apply to all symbols in market_data (assuming list of symbols for now)
        if isinstance(market_data, list):
            for symbol in market_data:
                signals[symbol] = base_score
        
        return signals

    def get_risk_factor(self) -> float:
        """
        Advanced risk factor based on HMM probabilities.
        """
        if self.regime == "BEAR":
            return 0.9
        elif self.regime == "BULL":
            return 0.2
        return 0.5

