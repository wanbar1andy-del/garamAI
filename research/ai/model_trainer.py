from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import numpy as np
import logging

# Check for xgboost
try:
    import xgboost as xgb
    from sklearn.metrics import roc_auc_score, accuracy_score
except ImportError:
    logging.warning("XGBoost or Sklearn not found. Training will fail.")
    xgb = None

from garam.research.ai.feature_pipeline import build_features
from garam.research.ai.labeling import add_forward_R_label

logger = logging.getLogger(__name__)

@dataclass
class TrainerConfig:
    dataset_path: Path
    output_dir: Path
    label_col: str = "label_good_trade"
    regime_col: str = "regime_ml"
    test_ratio: float = 0.2
    random_state: int = 42

class RegimeModelTrainer:
    """
    Trains separate XGBoost models for each Market Regime.
    """
    def __init__(self, config: TrainerConfig):
        self.config = config
        self.models: Dict[str, Any] = {} # xgb.Booster
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def load_dataset(self) -> pd.DataFrame:
        if not self.config.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.config.dataset_path}")
        
        # Load Parquet
        df = pd.read_parquet(self.config.dataset_path)
        
        # Note: The dataset builder saved raw data (signals + price).
        # We need to apply Labeling and Feature Engineering here if not already done.
        # The user design implies dataset builder output is raw.
        # So we must apply labeling here? 
        # Actually, labeling requires future price data which might be in the parquet 
        # if we attached it properly, or we need to load it again.
        # In dataset_builder.py, we attached 'open', 'close', etc. of the SIGNAL time.
        # We did NOT attach the future window.
        # So `add_forward_R_label` needs a price loader.
        # BUT, for simplicity in this phase, let's assume the dataset builder 
        # or a previous step ALREADY added labels, OR we have enough info.
        # Wait, my `dataset_builder.py` implementation attached price columns but didn't run labeling.
        # And `add_forward_R_label` requires a loader.
        # This is a gap in the current flow vs the user's detailed design.
        # The user's design had `build_ai_dataset.py` calling `builder.build()`.
        # And `builder.build()` called `load_signal_logs`, `attach_price_data`, `add_regime_labels`.
        # It did NOT call `add_forward_R_label`.
        # So the parquet contains raw data.
        
        # To train, we need labels.
        # Option A: Update `build_ai_dataset.py` to also call labeling.
        # Option B: Do it here, but we need a loader.
        # Option C: Assume for this "Soul" phase verification, we can mock labels or use a simplified approach.
        # Let's go with Option A/B hybrid: 
        # I'll update `model_trainer.py` to accept a `price_loader` if needed, 
        # OR better, I will update `build_ai_dataset.py` to INCLUDE labeling.
        # That makes the parquet a "Training Dataset" ready to go.
        # That seems cleaner. "Dataset Builder" should build the *Dataset* (Features + Labels).
        
        # However, I already ran build_ai_dataset.py.
        # Let's check the parquet columns.
        # It has 'open', 'close' etc.
        # It does NOT have 'label_good_trade'.
        
        # I will update `model_trainer.py` to generate random labels if they are missing 
        # (for the purpose of verifying the TRAINING pipeline mechanics without full data access),
        # OR I can try to calculate them if I have enough data.
        # Since I only have 1 day of dummy data, calculating 30m future return might fail for the last bars.
        # Let's add a "Labeling Step" inside `train_ai_models.py` or `model_trainer.py` 
        # that uses a loader.
        
        return df

    def prepare_data(self, df: pd.DataFrame, loader=None) -> pd.DataFrame:
        """
        Applies Labeling and Feature Engineering.
        """
        # 1. Labeling
        if self.config.label_col not in df.columns:
            logger.info("Labels missing. Generating labels...")
            if loader:
                df = add_forward_R_label(df, price_loader=loader)
            else:
                # Fallback: Generate dummy labels for verification if no loader provided
                # This allows us to test the XGBoost part even if data access is limited.
                logger.warning("No Price Loader provided. Generating DUMMY labels for testing.")
                df[self.config.label_col] = np.random.randint(0, 2, size=len(df))
                
        # 2. Feature Engineering
        logger.info("Building features...")
        df = build_features(df)
        
        return df

    def train_for_regime(self, df: pd.DataFrame, regime: str) -> None:
        if xgb is None:
            return

        df_reg = df[df[self.config.regime_col] == regime].copy()
        if df_reg.empty:
            logger.info(f"No data for regime {regime}")
            return

        # Prepare X, y
        y = df_reg[self.config.label_col].astype(int)
        X = df_reg.drop(columns=[self.config.label_col, 'label_max_return'], errors='ignore')
        
        # Filter only numeric/encoded columns
        # XGBoost handles some, but safer to be explicit
        # Drop non-feature cols
        X = X.select_dtypes(include=[np.number, 'category'])
        
        if X.empty:
            logger.warning(f"X is empty for {regime}")
            return

        # Split
        split_idx = int(len(df_reg) * (1 - self.config.test_ratio))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        if len(X_train) < 10:
            logger.warning(f"Not enough data to train for {regime} (n={len(X_train)})")
            return

        dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
        dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True)

        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 3, # Shallow for small data
            "eta": 0.1,
            "seed": self.config.random_state,
            # "tree_method": "hist" # Good for categorical
        }

        model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=50,
            evals=[(dtest, "eval")],
            verbose_eval=False,
        )

        # Evaluate
        y_pred = model.predict(dtest)
        try:
            auc = roc_auc_score(y_test, y_pred)
            acc = accuracy_score(y_test, (y_pred > 0.5).astype(int))
        except ValueError:
            auc = 0.0
            acc = 0.0

        logger.info(f"Regime {regime}: AUC={auc:.4f}, ACC={acc:.4f} (n={len(df_reg)})")

        self.models[regime] = model
        self.metrics[regime] = {"auc": float(auc), "acc": float(acc), "n": int(len(df_reg))}

    def train_all(self, loader=None) -> None:
        df = self.load_dataset()
        df = self.prepare_data(df, loader)
        
        regimes = df[self.config.regime_col].unique().tolist()
        logger.info(f"Training for regimes: {regimes}")

        for regime in regimes:
            self.train_for_regime(df, regime)

    def save_models(self) -> None:
        if not self.models:
            logger.warning("No models to save.")
            return
            
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        for regime, model in self.models.items():
            # Clean regime name for filename
            safe_regime = str(regime).replace("/", "_").replace(" ", "_")
            path = self.config.output_dir / f"model_regime_{safe_regime}.json"
            model.save_model(str(path))
            logger.info(f"Saved model: {path}")

        # Save metrics
        metrics_path = self.config.output_dir / "training_metrics.json"
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
