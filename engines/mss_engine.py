"""
Market Sensing Engine (MSS)
시장 감지 엔진

Role:
- Calculates 'Market Score' from Macro, Market Internal, and Sector indicators.
- Determines 'Risk Mode' (TURBO, NORMAL, ABS, EMERGENCY).
- Provides modifiers for Position Sizing and Risk Limits.
"""

import yaml
import logging
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
from garam.config import PATHS

logger = logging.getLogger("MSS")

class MarketSensingEngine:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.current_score = 0.0
        self.current_mode = "NORMAL"
        self.indicators = {} # Current indicator values
        
        # Stats
        self.history = []

    def _load_config(self, path: str = None) -> Dict:
        if path is None:
            # Default path
            path = PATHS.CONFIG_DIR / "mss_config.yaml"
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load MSS config from {path}: {e}")
            return {}

    def update_context(self, context: Dict[str, float]):
        """
        Update raw indicator values from external sources (DataFeeder).
        context: { 'exchange_rate_trend': 0.5, 'kospi_trend': -0.2, ... }
        """
        # Normalize/Clip inputs to -1.0 ~ 1.0 range just in case
        for k, v in context.items():
            self.indicators[k] = max(-1.0, min(1.0, float(v)))
            
        self._recalculate()

    def _recalculate(self):
        """
        Calculate Weighted Score based on config
        """
        if not self.config.get('system', {}).get('enabled', False):
            self.current_score = 0.0
            self.current_mode = "NORMAL"
            return

        total_score = 0.0
        total_weight = 0.0
        
        # Iterate Categories (macro, market, sector)
        ind_config = self.config.get('indicators', {})
        
        for category, cat_data in ind_config.items():
            cat_weight = cat_data.get('weight', 0.0)
            components = cat_data.get('components', {})
            
            cat_score = 0.0
            comp_weight_sum = 0.0
            
            for comp_name, comp_weight in components.items():
                # Get current value (default 0.0 if missing)
                val = self.indicators.get(comp_name, 0.0)
                cat_score += val * comp_weight
                comp_weight_sum += comp_weight
            
            # Normalize Category Score
            if comp_weight_sum > 0:
                cat_score /= comp_weight_sum
                
            total_score += cat_score * cat_weight
            total_weight += cat_weight
            
        # Final Score
        if total_weight > 0:
            self.current_score = total_score / total_weight
        else:
            self.current_score = 0.0
            
        self._determine_mode()
        
    def _determine_mode(self):
        """
        Determine Risk Mode based on Score and Thresholds
        """
        thresholds = self.config.get('thresholds', {})
        turbo = thresholds.get('turbo_threshold', 0.5)
        abs_val = thresholds.get('abs_threshold', -0.3)
        emergency = thresholds.get('emergency_threshold', -0.7)
        
        if self.current_score <= emergency:
            self.current_mode = "EMERGENCY"
        elif self.current_score <= abs_val:
            self.current_mode = "ABS"
        elif self.current_score >= turbo:
            self.current_mode = "TURBO"
        else:
            self.current_mode = "NORMAL"
            
        # Log change
        if self.history and self.history[-1]['mode'] != self.current_mode:
            logger.info(f"MSS Mode Changed: {self.history[-1]['mode']} -> {self.current_mode} (Score: {self.current_score:.2f})")
            
        self.history.append({
            'score': self.current_score,
            'mode': self.current_mode,
            'indicators': self.indicators.copy()
        })

    def get_decision_modifier(self) -> Dict[str, Any]:
        """
        Return modifiers for the Trading Engine
        """
        actions = self.config.get('actions', {})
        mode_actions = actions.get(self.current_mode, {})
        
        return {
            'mode': self.current_mode,
            'score': self.current_score,
            'size_multiplier': mode_actions.get('position_size_multiplier', 1.0),
            'max_positions': mode_actions.get('max_positions_override'), # Can be None
            'block_new_entry': mode_actions.get('block_new_entry', False),
            'force_liquidate': mode_actions.get('force_liquidate_all', False)
        }
