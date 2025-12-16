from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import pandas as pd
import json

try:
    import xgboost as xgb
except ImportError:
    xgb = None

from garam.research.ai.feature_pipeline import build_features

logger = logging.getLogger(__name__)

@dataclass
class AIAdapterConfig:
    model_root: Path
    regime_col: str = "regime_ml"

class AIAdapter:
    """
    Loads trained XGBoost models and scores live signals.
    Acts as a 'Soul' that adjusts risk based on learned probability of success.
    """
    def __init__(self, config: AIAdapterConfig):
        self.config = config
        self.models: Dict[str, Any] = {}
        self._load_models()

    def _load_models(self) -> None:
        if not self.config.model_root.exists():
            logger.warning(f"AI Model root not found: {self.config.model_root}")
            return

        if xgb is None:
            logger.warning("XGBoost not installed. AI Adapter disabled.")
            return

        for path in self.config.model_root.glob("model_regime_*.json"):
            try:
                # Extract regime name: model_regime_BULL_LOW_VOL.json -> BULL_LOW_VOL
                # Handle underscores correctly
                filename = path.stem
                regime = filename.replace("model_regime_", "")
                
                booster = xgb.Booster()
                booster.load_model(str(path))
                self.models[regime] = booster
                logger.info(f"Loaded AI model for regime: {regime}")
            except Exception as e:
                logger.error(f"Failed to load model {path}: {e}")

    def score_signal(
        self,
        regime: str,
        symbol: str,
        strategy_id: str,
        signal: int,
        features: Dict[str, Any],
    ) -> Optional[float]:
        """
        Returns p_good (0.0 - 1.0) for the given signal context.
        """
        if xgb is None:
            return None
            
        # If specific regime model missing, try 'unknown' or return None
        model = self.models.get(regime)
        if model is None:
            model = self.models.get('unknown')
            
        if model is None:
            return None

        # Construct single-row DataFrame
        feat_row = {f"feat_{k}": v for k, v in features.items()}
        
        row = {
            "symbol": symbol,
            "strategy_id": strategy_id,
            "signal": signal,
            self.config.regime_col: regime,
            **feat_row
        }
        
        df = pd.DataFrame([row])
        
        # Run pipeline (mostly for encoding, cleaning)
        df_processed = build_features(df)
        
        if df_processed.empty:
            return None
            
        # Align columns with model
        # XGBoost requires exact column match (names and order if not using DMatrix with feature_names, 
        # but even with DMatrix, extra columns can cause issues or mismatch warnings).
        if hasattr(model, 'feature_names') and model.feature_names:
            expected_cols = model.feature_names
            
            # 1. Add missing cols as NaN
            for col in expected_cols:
                if col not in df_processed.columns:
                    df_processed[col] = float('nan')
            
            # 2. Keep only expected cols and reorder
            df_processed = df_processed[expected_cols]
            
        # Prepare DMatrix
        # Must drop non-feature cols if any remain (handled by alignment above)
        X = df_processed
        
        # XGBoost DMatrix
        try:
            dmatrix = xgb.DMatrix(X, enable_categorical=True)
            proba = model.predict(dmatrix)[0]
            return float(proba)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None

    def adjust_risk(
        self,
        base_signal: int,
        base_risk_multiplier: float,
        p_good: Optional[float],
    ) -> Dict[str, Any]:
        """
        Adjusts signal and size based on AI confidence.
        Policy:
        - p < 0.4: Kill signal (0) or reduce size significantly.
        - 0.4 <= p < 0.6: Neutral (Keep base).
        - p >= 0.6: Boost size (up to 1.5x).
        """
        result = {
            "final_signal": base_signal,
            "final_risk_multiplier": base_risk_multiplier,
            "ai_confidence": p_good,
            "ai_adjustment": "none"
        }

        if p_good is None or base_signal == 0:
            return result

        if p_good < 0.4:
            # High probability of bad trade -> Suppress
            result["final_signal"] = 0
            result["final_risk_multiplier"] = 0.0
            result["ai_adjustment"] = "suppress"
        elif p_good >= 0.6:
            # High probability of good trade -> Boost
            # Cap at 1.5x
            boosted = min(base_risk_multiplier * 1.2, 1.5)
            result["final_risk_multiplier"] = boosted
            result["ai_adjustment"] = "boost"
            
        return result
