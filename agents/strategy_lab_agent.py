import logging
import itertools
from typing import Dict, Any, List, Callable
import pandas as pd
from ..alpha_lab.lab import AlphaLab

logger = logging.getLogger(__name__)

class StrategyLabAgent:
    """
    Offline Learning Agent.
    Uses AlphaLab to optimize strategy parameters based on historical data.
    """
    
    def __init__(self):
        self.lab = AlphaLab()
        logger.info("StrategyLabAgent initialized.")

    def run_optimization(self, 
                        base_config: Dict[str, Any], 
                        param_grid: Dict[str, List[Any]],
                        strategy_factory: Callable[[Dict], Callable]
                        ) -> Dict[str, Any]:
        """
        Run Grid Search Optimization.
        
        Args:
            base_config: Base experiment config (symbol, timeframe, etc.)
            param_grid: Dictionary of parameters to sweep { 'param_name': [values] }
            strategy_factory: Function that takes params dict and returns a strategy logic function
            
        Returns:
            Best parameters and performance metrics.
        """
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))
        
        logger.info(f"Starting optimization. Total combinations: {len(combinations)}")
        
        results = []
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            # Create strategy with these params
            strategy_logic = strategy_factory(params)
            
            # Update config
            config = base_config.copy()
            config['strategy'] = strategy_logic
            config['name'] = f"Opt_{params}"
            
            # Run Experiment
            # Note: AlphaLab loads data every time. For efficiency in v1, we should cache data in Lab.
            # But for now, it's fine.
            res = self.lab.run_experiment(config)
            
            if 'error' not in res:
                metrics = {
                    'params': params,
                    'return': res['total_return'],
                    'trades': res['total_trades']
                }
                results.append(metrics)
                logger.debug(f"Result for {params}: {metrics['return']:.2%}")
            else:
                logger.warning(f"Experiment failed for {params}: {res.get('error')}")
                
        # Find Best
        if not results:
            logger.warning("No successful experiments.")
            return {}
            
        # Simple criteria: Max Return
        best = max(results, key=lambda x: x['return'])
        
        logger.info(f"Optimization Complete. Best Return: {best['return']:.2%} with {best['params']}")
        return best

    def analyze_shadow_results(self, log_file: str):
        """
        Analyze Shadow Trading logs (Placeholder).
        """
        pass
