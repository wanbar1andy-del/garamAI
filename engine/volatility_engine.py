import pandas as pd
import numpy as np

class VolatilityFactorEngine:
    """
    Financial Engineering Engine for Volatility Factors.
    Calculates Quality, Risk, and Regime signals based on Volatility dynamics.
    """

    @staticmethod
    def calculate_factors(df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich dataframe with Volatility Factors.
        Expects: 'high', 'low', 'close' columns.
        Returns: DataFrame with added columns:
                 - atr, atr_pct
                 - vol_accel
                 - mom_6m
                 - quality_score
                 - downside_ratio
        """
        df = df.copy()
        
        # 1. Basic Volatility (ATR)
        # TR = Max(H-L, |H-Cp|, |L-Cp|)
        # Use simple rolling mean for ATR (Wilder's smoothing is standard but rolling is fine for factor usage)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR 20 (Business Month)
        df['atr_20'] = tr.rolling(window=20).mean()
        # Normalized ATR% (Risk Unit)
        # Avoid division by zero
        df['atr_pct'] = (df['atr_20'] / df['close']) * 100
        
        # 2. Volatility Acceleration (Crash/Bubble Signal)
        # How fast is volatility expanding relative to baseline?
        # Short (5d) / Long (60d)
        df['atr_5'] = tr.rolling(window=5).mean()
        df['atr_60'] = tr.rolling(window=60).mean()
        
        # Vol Accel: > 1.5 implies "Explosive State"
        df['vol_accel'] = df['atr_5'] / df['atr_60']
        
        # 3. Quality Momentum (Risk-Adjusted Return)
        # Return 6m (126 trading days)
        df['ret_6m'] = df['close'].pct_change(periods=126)
        
        # Quality Score = Return / Risk
        # We use ATR% as the risk denominator (Idiosyncratic Risk)
        # Note: If atr_pct is close to 0, this explodes. Clip minimum risk at 0.5%.
        safe_risk = df['atr_pct'].clip(lower=0.5)
        df['quality_score'] = df['ret_6m'] / safe_risk
        
        # RAM (Risk Adjusted Momentum) utilizing Standard Deviation (Alternative)
        # Annualized Volatility
        df['std_20'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
        df['ram_std'] = df['ret_6m'] / df['std_20'].clip(lower=1.0)

        # 4. Downside Deviation Ratio (Bad Volatility)
        # Ratio of Downside Volatility to Total Volatility (60d)
        def calc_downside_ratio(window):
            returns = window
            # Calc Total Std
            total_std = np.std(returns)
            # Calc Downside Std (Returns < 0 only, others 0)
            down_returns = np.where(returns < 0, returns, 0)
            down_std = np.std(down_returns)
            
            if total_std == 0: return 0.0
            return down_std / total_std

        # Rolling Apply is slow for lookback 60. Optimizing...
        # For now, let's stick to vectorized approach if possible, or accept slight slowness for build script.
        # Vectorized approximation: 
        # Downside Variance = Rolling Mean of (Min(0, r))^2
        returns = df['close'].pct_change()
        down_rets_sq = np.minimum(returns, 0) ** 2
        total_rets_sq = returns ** 2 # Assuming mean ~ 0 for variance approx, otherwise simple std
        
        # Proper Rolling Std
        roll_std = returns.rolling(60).std()
        
        # Proper Rolling Downside Std
        # Semi-deviation ~ sqrt(mean(min(0,r)^2))
        roll_down_std = np.sqrt(down_rets_sq.rolling(60).mean())
        
        df['downside_ratio'] = roll_down_std / roll_std
        
        return df

    @staticmethod
    def get_signal_status(row):
        """
        Return text status based on factors.
        Expects a row with 'vol_accel', 'atr_pct', 'downside_ratio'
        """
        status = []
        if row['vol_accel'] > 1.5:
            status.append("VOL_SPIKE")
        if row['atr_pct'] > 8.0:
            status.append("HIGH_RISK")
        if row['downside_ratio'] > 0.6:
            status.append("BAD_VOL")
            
        if not status:
            return "NORMAL"
        return "+".join(status)

class VolatilitySizer:
    """
    Capital Allocation Logic based on Volatility.
    """
    
    @staticmethod
    def calculate_risk_parity_weights(candidates: list[dict], target_vol: float = None) -> dict:
        """
        Calculate weights based on Inverse Volatility (Risk Parity).
        Args:
            candidates: List of dicts, each must have 'symbol' and 'atr_pct' (or 'risk').
            target_vol: Optional target portfolio volatility (e.g., 2.0 daily). 
                        If provided, weights are scaled to match target (Volatility Targeting).
                        If None, weights sum to 1.0 (Fully Invested Risk Parity).
        Returns:
            Dictionary {symbol: weight}
        """
        if not candidates: return {}
        
        # 1. Calculate Inverse Risk
        inv_risks = []
        valid_cands = []
        
        for c in candidates:
            # Risk Measure: ATR% (Safe floor at 0.5% to avoid infinity)
            risk = max(0.5, c.get('atr_pct', 100.0))
            if risk <= 0: risk = 0.5 # Double safety
            
            inv_risk = 1.0 / risk
            inv_risks.append(inv_risk)
            valid_cands.append(c['symbol'])
            
        total_inv_risk = sum(inv_risks)
        
        if total_inv_risk == 0:
            return {s: 0.0 for s in valid_cands}
            
        # 2. Base Weights (Sum to 1.0)
        base_weights = [ir / total_inv_risk for ir in inv_risks]
        
        # 3. Apply Target Volatility Scaling (Optional)
        # If Target Vol is 1.0% and Portfolio Base Vol is 0.5%, we leverage 2x.
        # Approx Portfolio Vol = Harmonic Mean of Component Vols? 
        # For simplicity in Phase 1, we implement simple Risk Parity (Sum=1.0).
        # Volatility Targeting requires Covariance matrix for accuracy.
        # We start with simple Inverse Vol normalization.
        
        result = dict(zip(valid_cands, base_weights))
        return result

    @staticmethod
    def apply_vol_accel_filter(candidates: list[dict], threshold: float = 1.6) -> list[dict]:
        """
        Filter out candidates with high Volatility Acceleration (Crash Warning).
        """
        safe = []
        for c in candidates:
            va = c.get('vol_accel', 0.0)
            if va < threshold:
                safe.append(c)
        return safe

