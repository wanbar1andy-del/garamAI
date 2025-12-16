import logging
from typing import Dict, Any, List
from .base import BaseEngine

logger = logging.getLogger(__name__)

class HybridController:
    """
    Manages the Dual Engine Architecture.
    - Loads Engine 1 (Legacy) and Engine 2 (Advanced).
    - Mixes signals based on configured weights.
    - Apply Dynamic Rules (Turbo/ABS).
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get("mode", "FIXED") # FIXED or DYNAMIC
        self.weights = config.get("weights", {"engine1": 0.5, "engine2": 0.5})
        
        self.engines: Dict[str, BaseEngine] = {}
        self.regime_status = "UNKNOWN" # Bull, Bear, Sideways

    def register_engine(self, engine: BaseEngine):
        """Register an engine instance."""
        self.engines[engine.name] = engine
        logger.info(f"Engine registered: {engine.name}")

    def update_weights(self, new_weights: Dict[str, float]):
        """Update mixing weights dynamically."""
        self.weights = new_weights
        logger.info(f"Weights updated: {self.weights}")

    def get_combined_signals(self, market_data: Any) -> Dict[str, float]:
        """
        Aggregates signals from all registered engines.
        Formula:
            Final_Score = Sum(Signal_i * Weight_i) / Sum(Weight_i)
        
        Dynamic Rules (Turbo/ABS):
            - Turbo (Bull): Engine 2 Weight *= turbo_multiplier (e.g., 2.0)
            - ABS (Bear): Engine 1 Weight *= abs_multiplier (e.g., 0.0 or 0.5)
        """
        combined_signals = {}
        
        # 1. Collect Signals
        engine_results = {}
        for name, engine in self.engines.items():
            try:
                engine_results[name] = engine.generate_signals(market_data)
            except Exception as e:
                logger.error(f"Error in engine {name}: {e}")
                engine_results[name] = {}

        # 2. Calculate Dynamic Weights
        # Base weights from config
        w1 = self.weights.get("engine1", 0.5)
        w2 = self.weights.get("engine2", 0.5)
        
        # Apply Regime Modifiers
        if self.mode == "DYNAMIC":
            rules = self.config.get("dynamic_rules", {})
            turbo_mult = rules.get("turbo_multiplier", 1.5)
            abs_mult = rules.get("abs_multiplier", 0.5)
            
            if self.regime_status == "BULL":
                # Turbo: Boost Advanced Engine
                # User Request: "200% -> ~63%". If w1=1, w2=1, turbo=2.0 -> w2=2. total=3. w2%=66%.
                w2 *= turbo_mult
                logger.info(f"TURBO ACTIVE: Boosting Engine 2 by x{turbo_mult} -> W2={w2}")
                
            elif self.regime_status == "BEAR":
                # ABS: Brake Legacy Engine (Reduce risk)
                w1 *= abs_mult
                logger.info(f"ABS ACTIVE: Reducing Engine 1 by x{abs_mult} -> W1={w1}")

        total_weight = w1 + w2
        if total_weight == 0:
            total_weight = 1.0 # Avoid div/0

        # 3. Aggregate
        all_symbols = set()
        for res in engine_results.values():
            all_symbols.update(res.keys())

        for symbol in all_symbols:
            s1 = engine_results.get("engine1", {}).get(symbol, 0.0)
            s2 = engine_results.get("engine2", {}).get(symbol, 0.0)
            
            # Weighted Average
            final_score = (s1 * w1 + s2 * w2) / total_weight
            combined_signals[symbol] = final_score

        return combined_signals

    def _calculate_modifiers(self) -> Dict[str, float]:
        """Deprecated: Logic moved to get_combined_signals for better visibility"""
        return {}

    def set_regime(self, regime: str):
        """External update of market regime (from HMM)"""
        self.regime_status = regime
