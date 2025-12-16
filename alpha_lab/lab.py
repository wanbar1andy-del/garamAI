import logging
from typing import Dict, List, Any, Callable
import pandas as pd
from ..data.lake_manager import LakeManager
from ..features.factory import FeatureFactory
from .backtest.engine import BacktestEngine

logger = logging.getLogger(__name__)

class AlphaLab:
    """
    Research environment for testing hypotheses (1+1 conditions).
    Orchestrates Data Lake -> Feature Factory -> Backtest Engine.
    """
    
    def __init__(self):
        self.lake = LakeManager()
        self.factory = FeatureFactory()
        self.engine = BacktestEngine()
        logger.info("AlphaLab initialized.")

    def run_experiment(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single experiment.
        
        Config:
            - symbol: str
            - timeframe: str
            - start_date: str
            - end_date: str
            - features: List[Dict] (for FeatureFactory)
            - strategy: Callable (for BacktestEngine)
            - name: str
        """
        name = experiment_config.get('name', 'Unnamed')
        logger.info(f"Running experiment: {name}")
        
        # 1. Load Data
        df = self.lake.get_price_history(
            symbol=experiment_config['symbol'],
            timeframe=experiment_config['timeframe'],
            start_date=experiment_config.get('start_date'),
            end_date=experiment_config.get('end_date')
        )
        
        if df.empty:
            logger.error("No data found for experiment.")
            return {'error': 'No data'}
            
        # 2. Compute Features
        df = self.factory.compute_features(df, experiment_config.get('features', []))
        
        # 3. Run Backtest
        strategy_logic = experiment_config.get('strategy')
        if not strategy_logic:
            logger.error("No strategy logic provided.")
            return {'error': 'No strategy'}
            
        results = self.engine.run(df, strategy_logic)
        results['name'] = name
        
        return results

    def compare_results(self, results_list: List[Dict[str, Any]]):
        """Compare multiple experiment results."""
        summary = []
        for res in results_list:
            if 'error' in res:
                continue
            summary.append({
                'name': res.get('name'),
                'return': res.get('total_return'),
                'trades': res.get('total_trades'),
                'final_equity': res.get('final_equity')
            })
        return pd.DataFrame(summary)
