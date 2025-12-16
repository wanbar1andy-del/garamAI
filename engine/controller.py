from typing import Dict, Any, List
import logging
import yaml
from pathlib import Path
try:
    from garam.config import PATHS
except ImportError:
    from config import PATHS
from .legacy import LegacyEngine
from .advanced import AdvancedEngine

logger = logging.getLogger("HybridController")

class HybridController:
    """
    Dual Engine Controller
    
    Roles:
    - Loads Engine 1 (Legacy) and Engine 2 (Advanced).
    - Orchestator: Calls engines and mixes signals.
    - Implements Turbo (Acceleration) and ABS (Brake) logic.
    """
    
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        
        # Initialize Engines
        self.engine1 = LegacyEngine()
        self.engine2 = AdvancedEngine()
        
        logger.info("HybridController Initialized (Dual Engine Architecture).")

    def _load_config(self, path: Path = None) -> Dict:
        if path is None:
            path = PATHS.CONFIG_DIR / "engine_config.yaml"
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load engine config: {e}")
            return {}

    def run_cycle(self, date: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main Execution Cycle.
        
        1. Get Signals from Engine 1 (Alpha/Technical).
        2. Get Directives from Engine 2 (MSS/Macro).
        3. Mix and Modulate.
        """
        
        # 1. Engine 1 Analysis
        e1_result = self.engine1.analyze(date, context)
        base_signals = e1_result.get('signals', {})
        
        # 2. Engine 2 Analysis
        # Extract MSS-specific data from context if needed, or pass whole context
        e2_result = self.engine2.analyze(date, context)
        directives = e2_result.get('directives', {})
        
        # 3. Mixing & Modulation
        final_signals, status_meta, effective_directives = self._mix_signals(base_signals, directives)
        
        # 4. Consolidate Metadata for Reporting
        meta = {
            'engine1_meta': e1_result.get('meta', {}),
            'engine2_meta': e2_result.get('meta', {}),
            'controller_status': status_meta
        }
        
        return {
            'signals': final_signals,
            'meta': meta,
            'directives': effective_directives
        }

    def _mix_signals(self, signals: Dict[str, float], directives: Dict[str, Any]) -> tuple:
        """
        Apply Controller Logic: Turbo, ABS, Normal.
        Returns: (final_signals, status_meta, effective_directives)
        """
        mode = directives.get('mode', 'NORMAL')
        size_multiplier = directives.get('size_multiplier', 1.0)
        force_liquidate = directives.get('force_liquidate', False)
        
        # Config Overrides
        ctrl_config = self.config.get('controller', {})
        
        final_signals = signals.copy()
        status = f"Mode: {mode}"
        
        # Effective Directives (to be returned)
        eff_directives = {
            'mode': mode,
            'size_multiplier': size_multiplier, # Default/Input
            'force_liquidate': force_liquidate
        }
        
        if force_liquidate or mode == 'EMERGENCY':
            logger.warning("🚨 CONTROLLER: ABS Triggered (Emergency Liquidate)")
            eff_directives['mode'] = 'EMERGENCY'
            eff_directives['action'] = 'LIQUIDATE_ALL'
            return {}, {'mode': 'EMERGENCY', 'action': 'LIQUIDATE_ALL'}, eff_directives
            
        if mode == 'TURBO':
            # Boost Multiplier
            boost = ctrl_config.get('turbo_multiplier', size_multiplier)
            logger.info(f"🔥 CONTROLLER: Turbo Activated (Multiplier: {boost}x)")
            
            # Apply to signals (Logic boost)
            for sym in final_signals:
                final_signals[sym] *= boost
                
            status += f" (Boost {boost}x)"
            eff_directives['size_multiplier'] = boost # Update with actual boost used
            
        elif mode == 'ABS':
            # Brake Multiplier
            brake = ctrl_config.get('abs_multiplier', size_multiplier)
            logger.info(f"🛑 CONTROLLER: ABS Activated (Multiplier: {brake}x)")
            
            for sym in final_signals:
                final_signals[sym] *= brake
                
            status += f" (Cut {brake}x)"
            eff_directives['size_multiplier'] = brake # Update with actual brake used
            
        return final_signals, {'mode': mode, 'desc': status}, eff_directives
