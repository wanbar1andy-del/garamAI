from pathlib import Path
import pandas as pd
import yaml
import json
import numpy as np

class RegimeSummaryBuilder:
    def __init__(self, data_dir: Path, config_path: Path):
        self.data_dir = data_dir          # g:/.../garamdata/history
        self.config_path = config_path    # config/regime_strategy_matrix.yaml

    def load_labeled_data(self, fname: str) -> pd.DataFrame:
        path = self.data_dir / fname
        if not path.exists():
            print(f"Warning: File not found: {path}")
            return pd.DataFrame()
            
        df = pd.read_csv(path, parse_dates=["timestamp"]) # timestamp from label_20y_regimes.py
        return df

    def load_strategy_matrix(self) -> dict:
        if not self.config_path.exists():
            print(f"Warning: Config not found: {self.config_path}")
            return {}
            
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _calc_cagr(self, df: pd.DataFrame) -> float:
        if df.empty: return 0.0
        # Simple CAGR approximation for regime slices (not strictly accurate for discontinuous periods but good for comparison)
        # Using average daily return * 252
        avg_daily_ret = df['ret'].mean()
        return (1 + avg_daily_ret) ** 252 - 1

    def _calc_sharpe(self, returns: pd.Series) -> float:
        if returns.std() == 0: return 0.0
        return (returns.mean() / returns.std()) * np.sqrt(252)

    def _calc_max_dd(self, prices: pd.Series) -> float:
        if prices.empty: return 0.0
        # Reconstruct a price series from returns for the regime to calculate DD within that regime context
        # Or just use the raw prices if they are continuous. 
        # Since regime data is discontinuous, MaxDD is tricky. 
        # We will calculate MaxDD of the *strategy equity curve* if we had one, but here we only have raw prices.
        # Let's calculate MaxDD of the underlying asset during that regime as a proxy for "Market Risk" in that regime.
        
        # However, prices are not continuous. 
        # Let's just use the min/max of the chunks or just skip for now if too complex for this summary.
        # Better approach: Calculate MaxDD of the concatenated regime series (treating it as one long period).
        
        cum_ret = (1 + prices.pct_change().fillna(0)).cumprod()
        peak = cum_ret.cummax()
        dd = (cum_ret - peak) / peak
        return dd.min()

    def compute_stats_for_regime(self, df: pd.DataFrame, regime: str) -> dict:
        # Filter for regime
        sub = df[df["state"] == regime].copy() # 'state' from label_20y_regimes.py
        if sub.empty:
            return {}

        # Calculate returns
        sub["ret"] = sub["close"].pct_change().fillna(0.0)
        
        cagr = self._calc_cagr(sub)
        sharpe = self._calc_sharpe(sub["ret"])
        max_dd = self._calc_max_dd(sub["close"])

        return {
            "cagr": float(round(cagr, 4)),
            "sharpe": float(round(sharpe, 2)),
            "max_dd": float(round(max_dd, 4)),
            "win_rate": float(round((sub["ret"] > 0).mean(), 2)),
            "avg_R": float(round(sub["ret"].mean() / sub["ret"].abs().mean(), 2)) if sub["ret"].abs().mean() != 0 else 0.0
        }

    def build_summary(self, labeled_fname: str, out_path: Path):
        df = self.load_labeled_data(labeled_fname)
        if df.empty:
            print("No data to process.")
            return

        matrix = self.load_strategy_matrix()
        if not matrix:
            print("No strategy matrix found.")
            return

        summary = {}
        for regime, cfg in matrix.items():
            stats = self.compute_stats_for_regime(df, regime)
            summary[regime] = {
                "strategy": cfg.get("strategy", "Unknown"),
                "params": cfg.get("params", {}),
                "historical_stats": stats
            }

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"Saved regime summary to {out_path}")
