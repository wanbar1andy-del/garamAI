
import json
from pathlib import Path
from datetime import datetime

class TacticalGenome:
    """
    [ACTIVE PARAMETER DNA]
    The Central Nervous System of OSS.
    Stores 'Experience' and 'Evolved Parameters'.
    This IS the OSS's current state of wisdom.
    """
    def __init__(self):
        # Default starting DNA
        self.params = {
            # --- Defense (Shark Radar) ---
            "whale_min_val": 100_000_000,
            "shakeout_vol_drop": 0.5,
            "liquidity_guard_ratio": 0.30,
            
            # --- Offense (Typhoon) ---
            "impact_power_min": 0.03,
            "impact_power_max": 0.07,
            "typhoon_acc_threshold": 5.0,
            
            # --- Formation (Pulse) ---
            "pulse_support_buffer": 0.05,
            "trailing_stop_pct": 0.07,
            
            # --- Solo Mode (Guerrilla) ---
            "solo_oss_threshold": 7.2,      # Lowered from 8.0
            "solo_trailing_stop": 0.03,     # Tighter stop (3%)
            "solo_capital_limit": 300_000_000 # Below 300M is 'Solo'
        }
        self.memory = [] # Experience Log
        self.config_path = Path("core/active_config/tactical_dna.json")
        self._load_or_create()

    def _load_or_create(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.params.update(data.get("params", {}))
                    self.memory = data.get("memory", []) 
            except Exception as e:
                print(f"[DNA LOAD ERROR] {e}. Using Defaults.")
        else:
            self.save()

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({"params": self.params, "memory": self.memory}, f, indent=4)
            
    def get(self, key):
        return self.params.get(key, 0)

    def remember(self, context: dict, action: str, outcome: dict):
        """
        [EXPERIENCE LOGGING]
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "action": action,
            "outcome": outcome
        }
        self.memory.append(event)
        self.save()

    def reflect(self):
        """
        [WISDOM GENERATION]
        """
        print(f"\n[OSS REFLECTION] Analyzing {len(self.memory)} Experiences...")
        
        # 1. Liquidity Guard Analysis
        traps = [m for m in self.memory if m['outcome'].get('result') == 'TRAPPED']
        if len(traps) > 0:
            print(f"   -> Found {len(traps)} painful Exit Failures.")
            old_val = self.params.get("liquidity_guard_ratio", 0.3)
            self.params["liquidity_guard_ratio"] = old_val * 0.9 
            print(f"   [EVOLUTION] Liquidity Guard: {old_val:.2f} -> {self.params['liquidity_guard_ratio']:.2f}")
        
        # 2. Typhoon Analysis
        fizzles = [m for m in self.memory if m['outcome'].get('result') == 'FIZZLE']
        if len(fizzles) > 0:
            print(f"   -> Found {len(fizzles)} Typhoon failures.")
            self.params["impact_power_min"] = self.params.get("impact_power_min", 0.03) * 1.1 
            self.params["impact_power_max"] = self.params.get("impact_power_max", 0.07) * 1.1
            
        self.save()

# Global Instance
dna = TacticalGenome()
