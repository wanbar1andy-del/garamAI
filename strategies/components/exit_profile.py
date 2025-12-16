"""
Exit Profile Table
Stores optimal exit parameters for each Micro-Regime and Mode.
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ExitParams:
    time_stop_bars: int
    target_r: float
    stop_r: float = -0.7 # Fixed default risk
    use_trailing: bool = False
    trailing_beta: float = 0.0

class ExitProfileTable:
    """
    Lookup table for Exit Parameters.
    """
    
    def __init__(self):
        # Key: (micro_regime, mode)
        # Mode: "ATTACK", "BALANCED", "DEFENSE"
        self.profiles: Dict[tuple, ExitParams] = {}
        self._init_profiles()
        
    def _init_profiles(self):
        """Initialize with Research Values (v0.3)"""
        
        # --- STRONG UP ---
        # Attack: Ride the trend (120m+, 3R+)
        # Defense: Still bullish but tighter
        for vol in ["HIGH_VOL", "MED_VOL", "LOW_VOL"]:
            regime = f"STRONG_UP_{vol}"
            
            # High Vol needs more room? Actually research showed 120m for High Vol.
            # Low Vol showed 30m? Wait, research said:
            # STRONG_UP_HIGH_VOL -> 120m
            # STRONG_UP_LOW_VOL -> 30m (Maybe because low vol trends are smoother/faster or just noise?)
            # Let's follow the Matrix logic generally but respect data.
            
            if vol == "HIGH_VOL":
                self.profiles[(regime, "ATTACK")] = ExitParams(120, 3.0, -0.7, True, 0.5)
                self.profiles[(regime, "DEFENSE")] = ExitParams(60, 2.0, -0.7, False)
            else:
                # Low/Med Vol
                self.profiles[(regime, "ATTACK")] = ExitParams(60, 3.0, -0.7, True, 0.3)
                self.profiles[(regime, "DEFENSE")] = ExitParams(30, 2.0, -0.7, False)

        # --- WEAK UP ---
        # Balanced approach
        for vol in ["HIGH_VOL", "MED_VOL", "LOW_VOL"]:
            regime = f"WEAK_UP_{vol}"
            self.profiles[(regime, "ATTACK")] = ExitParams(60, 2.5, -0.7, True, 0.5)
            self.profiles[(regime, "BALANCED")] = ExitParams(60, 2.0, -0.7, False)
            self.profiles[(regime, "DEFENSE")] = ExitParams(30, 1.5, -0.7, False)

        # --- FLAT / SIDEWAYS ---
        # Defense: Quick scalp (16-30m)
        for vol in ["HIGH_VOL", "MED_VOL", "LOW_VOL"]:
            regime = f"FLAT_{vol}"
            # Even in Attack mode, Flat market doesn't support long holds
            self.profiles[(regime, "ATTACK")] = ExitParams(30, 2.0, -0.7, False) 
            self.profiles[(regime, "DEFENSE")] = ExitParams(16, 1.5, -0.7, False)

        # --- DOWN ---
        # Defense: Survival
        for trend in ["WEAK_DOWN", "STRONG_DOWN"]:
            for vol in ["HIGH_VOL", "MED_VOL", "LOW_VOL"]:
                regime = f"{trend}_{vol}"
                self.profiles[(regime, "ATTACK")] = ExitParams(30, 1.5, -0.7, False) # Counter-trend scalp
                self.profiles[(regime, "DEFENSE")] = ExitParams(16, 1.0, -0.7, False)

    def get_params(self, micro_regime: str, mode: str = "ATTACK") -> ExitParams:
        """
        Get exit parameters. Falls back to safe defaults if not found.
        """
        # Try exact match
        if (micro_regime, mode) in self.profiles:
            return self.profiles[(micro_regime, mode)]
            
        # Try fallback mode (if ATTACK not found, try DEFENSE)
        if (micro_regime, "DEFENSE") in self.profiles:
            return self.profiles[(micro_regime, "DEFENSE")]
            
        # Default Fallback (Safe)
        return ExitParams(16, 1.5, -0.7, False)
