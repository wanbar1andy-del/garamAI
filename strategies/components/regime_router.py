import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from regime.edge_meter import EdgeMeter

@dataclass
class MarketState:
    """Snapshot of market indicators for regime classification"""
    trend_20d: float       # 20-day return
    atr_z: float           # Normalized ATR (0~1 percentile)
    fm: float              # Daily Trend Score
    fs_orb: float          # Intraday ORB Score
    fs_fast: float         # Intraday Momentum Score
    timestamp: str         # Current timestamp

@dataclass
class ModuleConfig:
    """Configuration for the selected module"""
    regime_id: str
    module_id: str
    params: Dict
    intensity: float

class RegimeRouter:
    """
    Routes MarketState to a specific Regime and Module.
    """
    def __init__(self, playbook_path: Path):
        self.playbook = self._load_playbook(playbook_path)
        self.edge_meter = EdgeMeter()
        
    def _load_playbook(self, path: Path) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def classify_regime(self, state: MarketState) -> str:
        """
        Classify MarketState into R1~R7 using EdgeMeter.
        """
        return self.edge_meter.classify_regime(state)
                
    def select_module(self, state: MarketState) -> ModuleConfig:
        """
        Select module and params based on MarketState.
        """
        regime_id = self.classify_regime(state)
        
        # Get Regime Config
        regime_conf = self.playbook['regimes'].get(regime_id)
        if not regime_conf:
            # Fallback to R7 if unknown
            regime_id = "R7_EVENT_RISK_OFF"
            regime_conf = self.playbook['regimes'][regime_id]
            
        module_id = regime_conf['module']
        intensity = regime_conf.get('intensity_step', regime_conf.get('intensity', 0.5))
        
        # Get Module Config
        # Get Module Config
        if 'modules' in self.playbook:
            module_conf = self.playbook['modules'].get(module_id)
            base_params = module_conf['base'].copy()
            
            # Apply Intensity Scaling (Simple Linear for v1)
            final_params = base_params.copy()
            if 'risk_pct_base' in base_params:
                final_params['risk_pct'] = base_params['risk_pct_base'] * intensity
        else:
            # Playbook v3 style (params embedded)
            final_params = regime_conf.get('params', {}).copy()
        
        # Adjust Target/Time Stop based on Intensity if needed (Future)
        # For now, base params in YAML are already tuned for the regime.
        
        return ModuleConfig(
            regime_id=regime_id,
            module_id=module_id,
            params=final_params,
            intensity=intensity
        )
