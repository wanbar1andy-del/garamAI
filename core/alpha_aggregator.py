import pandas as pd
import yaml
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from garam.config import PATHS
except ImportError:
    from config import PATHS
try:
    from garam.alphas.base_alpha import BaseAlpha
except ImportError:
    from alphas.base_alpha import BaseAlpha

logger = logging.getLogger(__name__)

class AlphaAggregator:
    def __init__(self, catalog_path: Path = None):
        self.catalog_path = catalog_path or (PATHS.CONFIG_DIR / "alpha_catalog.yaml")
        self.alphas: Dict[str, BaseAlpha] = {}
        self.alpha_configs: Dict[str, dict] = {}
        
        self._load_catalog()
        self._initialize_alphas()
        
    def _load_catalog(self):
        """Load alpha definitions from YAML catalog."""
        if not self.catalog_path.exists():
            logger.error(f"Alpha catalog not found at {self.catalog_path}")
            return
            
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.alpha_configs = {item['id']: item for item in data.get('alphas', [])}
            
    def _initialize_alphas(self):
        """Dynamically import and instantiate alpha classes."""
        import inspect
        
        for alpha_id, config in self.alpha_configs.items():
            state = config.get('state', 'DISABLED')
            if state not in ['ACTIVE', 'EXPERIMENT']:
                continue
                
            try:
                # Convention: id="A3_box_meanrev" -> module="garam.alphas.a3_box_meanrev"
                # OR use explicit 'module' field in config
                if 'module' in config:
                    module_name = f"garam.alphas.{config['module']}"
                else:
                    module_name = f"garam.alphas.{alpha_id.lower()}"
                
                # Dynamic Import
                module = importlib.import_module(module_name)
                
                # Find class that inherits from BaseAlpha
                alpha_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseAlpha) and obj is not BaseAlpha:
                        alpha_class = obj
                        break
                
                if alpha_class:
                    self.alphas[alpha_id] = alpha_class(alpha_id, config)
                    logger.info(f"Initialized Alpha: {alpha_id} ({alpha_class.__name__})")
                else:
                    logger.warning(f"No BaseAlpha subclass found in {module_name}")
                
            except ImportError:
                logger.warning(f"Module not found for {alpha_id} ({module_name})")
            except Exception as e:
                logger.error(f"Failed to init {alpha_id}: {e}")

    def compute_final_score(self, market_data: dict, universe: list, regime: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compute final weighted score for all symbols.
        
        Args:
            market_data: Dictionary of DataFrames (daily_close, etc.)
            universe: List of symbols
            regime: Current market regime (e.g., 'R3_UP_BOX')
            
        Returns:
            final_scores: DataFrame (Index=Date, Columns=Symbols)
            alpha_breakdown: DataFrame (Index=Date, Columns=MultiIndex(AlphaID, Symbol)) or similar structure?
                             For simplicity, maybe just return the weighted sum for now.
        """
        if not self.alphas:
            logger.warning("No active alphas to compute.")
            return pd.DataFrame(), pd.DataFrame()
            
        # 1. Compute scores for each active alpha
        raw_scores = {}
        weighted_scores_sum = None
        
        for alpha_id, alpha in self.alphas.items():
            # Check if alpha is active in this regime (optional optimization, 
            # but usually we compute all and weight by 0 if not needed, to track shadow performance)
            
            # Get weight for current regime
            weights = alpha.config.get('regime_weights', {})
            w = weights.get(regime, 0.0)
            
            # Debug
            logger.info(f"Alpha {alpha_id} weight for {regime}: {w}")
            
            # Compute raw score
            try:
                score_df = alpha.compute_scores(market_data, universe)
                if score_df.empty:
                    continue
                    
                raw_scores[alpha_id] = score_df
                
                # Apply Weight
                if w > 0:
                    weighted_score = score_df * w
                    
                    if weighted_scores_sum is None:
                        weighted_scores_sum = weighted_score.fillna(0)
                    else:
                        weighted_scores_sum = weighted_scores_sum.add(weighted_score.fillna(0), fill_value=0)
                    
                    # Track total weight for normalization?
                    # The spec says: FinalScore = Sum(Score * W) / Sum(W)
                    # But current implementation just Sums?
                    # If I just Sum, then (80*1 + -1*1) = 79.
                    # If I don't normalize, the scale depends on how many alphas are active.
                    # I SHOULD normalize by sum of weights.
            except Exception as e:
                logger.error(f"Error computing {alpha_id}: {e}")
                
        if weighted_scores_sum is None:
            return pd.DataFrame(), pd.DataFrame()
            
        # Normalize by total weight
        # We need to calculate total weight per symbol? Or just global scalar if weights are static?
        # Weights are static per regime.
        total_weight = sum(alpha.config.get('regime_weights', {}).get(regime, 0.0) for alpha in self.alphas.values())
        
        if total_weight > 0:
            final_scores = weighted_scores_sum / total_weight
        else:
            final_scores = weighted_scores_sum # Avoid div by zero
            
        return final_scores, raw_scores

if __name__ == "__main__":
    # Simple Test
    logging.basicConfig(level=logging.INFO)
    agg = AlphaAggregator()
    print("Active Alphas:", list(agg.alphas.keys()))
