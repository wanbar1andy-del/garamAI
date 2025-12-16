import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import joblib
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

class HMMRegimeDetector:
    """
    Detects market regime using Hidden Markov Model (GaussianHMM).
    Regimes: 0 (Bull/Change), 1 (Bear/Volatile), 2 (Sideways) - Interpretation depends on training.
    """
    def __init__(self, n_components=3, covariance_type="full", n_iter=1000):
        self.model = GaussianHMM(n_components=n_components, covariance_type=covariance_type, n_iter=n_iter)
        self.is_fitted = False
        self.regime_map = {0: "UNKNOWN", 1: "UNKNOWN", 2: "UNKNOWN"}

    def train(self, historical_prices: pd.Series):
        """
        Train HMM on historical price data (Close prices).
        Features: Log Returns, Volatility (Range).
        """
        if len(historical_prices) < 100:
            logger.warning("Not enough data to train HMM.")
            return

        # Feature Engineering
        returns = np.log(historical_prices / historical_prices.shift(1)).dropna()
        volatility = returns.rolling(window=20).std().dropna()
        
        # Align data
        common_index = returns.index.intersection(volatility.index)
        X = np.column_stack([returns.loc[common_index], volatility.loc[common_index]])

        # Fit Model
        logger.info("Training HMM model...")
        self.model.fit(X)
        self.is_fitted = True
        
        # Heuristic to map states to regimes
        # Calculate mean return and volatility for each state
        means = self.model.means_
        # means[:, 0] = returns mean, means[:, 1] = volatility mean
        
        # Sort states by volatility (assuming high vol = Bear/Panic)
        sorted_by_vol = np.argsort(means[:, 1])
        
        # Simple Mapping Heuristic
        # Lowest Vol -> Bull (or Sideways if return is low)
        # Highest Vol -> Bear/Panic
        
        self.regime_map[sorted_by_vol[0]] = "BULL" # Low Vol
        self.regime_map[sorted_by_vol[1]] = "SIDEWAYS" # Mid Vol
        self.regime_map[sorted_by_vol[2]] = "BEAR" # High Vol
        
        logger.info(f"HMM Trained. Regime Map: {self.regime_map}")
        logger.info(f"State Means (Ret, Vol): \n{means}")

    def predict_regime(self, recent_prices: pd.Series) -> str:
        """
        Predict the current regime based on recent price history.
        """
        if not self.is_fitted:
            logger.warning("HMM model not fitted. Returning UNKNOWN.")
            return "UNKNOWN"

        try:
            # Prepare features for the sequence
            returns = np.log(recent_prices / recent_prices.shift(1)).dropna()
            volatility = returns.rolling(window=20).std().dropna()
            
            common_index = returns.index.intersection(volatility.index)
            if len(common_index) == 0:
                return "UNKNOWN"
                
            X = np.column_stack([returns.loc[common_index], volatility.loc[common_index]])
            
            # Predict sequence
            hidden_states = self.model.predict(X)
            current_state = hidden_states[-1]
            
            return self.regime_map.get(current_state, "UNKNOWN")
        except Exception as e:
            logger.error(f"HMM Prediction failed: {e}")
            return "UNKNOWN"

    def save_model(self, path: str):
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        self.model = joblib.load(path)
        self.is_fitted = True
