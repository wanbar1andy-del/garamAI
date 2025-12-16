"""
Surfing Brain v1
Coordination layer for Regime, Mode, and Risk control.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
from pathlib import Path
import sys
import yaml
from datetime import datetime
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

class Regime(str, Enum):
    EAT = "EAT"     # 먹는 장
    HURT = "HURT"   # 아픈 장
    DEATH = "DEATH" # 죽는 장

class Mode(str, Enum):
    SHIELD = "SHIELD"
    CRUISE = "CRUISE"
    ATTACK = "ATTACK"

class SurfState(str, Enum):
    SINGLE_MODEL = "SINGLE_MODEL"
    MULTI_MODEL = "MULTI_MODEL"

@dataclass
class SurfingContext:
    timestamp: str
    regime: Regime
    uncertainty: float             # 0.0 ~ 1.0
    recent_expectancy_R: float     # recent average R
    recent_drawdown_pct: float
    kr_pnl_recent: float = 0.0
    us_pnl_recent: float = 0.0

@dataclass
class SurfingDecision:
    mode: Mode
    surf_state: SurfState
    risk_multiplier: float
    exit_aggressiveness: float     # 0.0~1.0 (0=loose, 1=tight)
    allocation_kr: float           # 0.0~1.0
    allocation_us: float           # 0.0~1.0
    allocation_cash: float         # 0.0~1.0
    notes: str = ""

class SurfingBrain:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or PATHS.CONFIG_DIR / "surfing_mode_rules.yaml"
        self.config = self._load_config()
        self.log_dir = PATHS.LOGS_DIR / "surfing_decisions"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def evaluate(self, ctx: SurfingContext) -> SurfingDecision:
        """
        Main entry point. Given current market & performance context,
        returns a SurfingDecision (mode, risk, allocation).
        """
        # 1. Determine Mode
        mode = self._determine_mode(ctx)
        
        # 2. Determine Surf State
        surf_state = self._determine_surf_state(ctx)
        
        # 3. Get Parameters for Mode
        params = self.config['mode_parameters'].get(mode.value, {})
        
        decision = SurfingDecision(
            mode=mode,
            surf_state=surf_state,
            risk_multiplier=params.get('risk_multiplier', 1.0),
            exit_aggressiveness=params.get('exit_aggressiveness', 0.5),
            allocation_kr=params.get('allocation_kr', 0.4),
            allocation_us=params.get('allocation_us', 0.4),
            allocation_cash=params.get('allocation_cash', 0.2),
            notes=f"Regime: {ctx.regime}, Uncertainty: {ctx.uncertainty:.2f}"
        )
        
        # 4. Log Decision
        self._log_decision(ctx, decision)
        
        return decision

    def _determine_mode(self, ctx: SurfingContext) -> Mode:
        rules = self.config.get('mode_rules', {})
        thresholds = self.config.get('uncertainty_thresholds', {})
        dd_thresholds = self.config.get('drawdown_thresholds', {})
        exp_thresholds = self.config.get('recent_expectancy_thresholds', {})
        
        # Helper to resolve threshold values
        def resolve_val(val, lookup):
            if isinstance(val, str) and val in lookup:
                return lookup[val]
            return float(val)

        # Check SHIELD
        if self._check_conditions(ctx, rules.get('shield', {}).get('conditions', []), thresholds, dd_thresholds, exp_thresholds):
            return Mode.SHIELD
            
        # Check ATTACK
        if self._check_conditions(ctx, rules.get('attack', {}).get('conditions', []), thresholds, dd_thresholds, exp_thresholds):
            return Mode.ATTACK
            
        # Default CRUISE
        return Mode.CRUISE

    def _check_conditions(self, ctx: SurfingContext, conditions: list, uncert_th, dd_th, exp_th) -> bool:
        if not conditions:
            return False
            
        for cond in conditions:
            # Simple parser for "variable operator value"
            # e.g. "regime == DEATH", "uncertainty >= high"
            parts = cond.split()
            if len(parts) != 3:
                continue
                
            var, op, val_str = parts
            val_str = val_str.strip('"').strip("'")
            
            # Resolve variable from context
            ctx_val = getattr(ctx, var, None)
            if var == 'regime':
                ctx_val = ctx.regime.value
            
            # Resolve threshold value
            limit_val = val_str
            if var == 'uncertainty':
                limit_val = uncert_th.get(val_str, float(val_str) if val_str.replace('.','',1).isdigit() else 0.5)
            elif var == 'recent_drawdown_pct':
                limit_val = dd_th.get(val_str, float(val_str) if val_str.replace('.','',1).isdigit() else 0.1)
            elif var == 'recent_expectancy_R':
                limit_val = exp_th.get(val_str, float(val_str) if val_str.replace('.','',1).isdigit() else 0.0)
            elif val_str.replace('.','',1).isdigit():
                limit_val = float(val_str)
                
            # Compare
            match = False
            if op == '==':
                match = str(ctx_val) == str(limit_val)
            elif op == '>=':
                match = float(ctx_val) >= float(limit_val)
            elif op == '<=':
                match = float(ctx_val) <= float(limit_val)
            elif op == '>':
                match = float(ctx_val) > float(limit_val)
            elif op == '<':
                match = float(ctx_val) < float(limit_val)
            
            if not match:
                # print(f"Condition failed: {var} ({ctx_val}) {op} {limit_val}")
                return False
                
        return True

    def _determine_surf_state(self, ctx: SurfingContext) -> SurfState:
        rules = self.config.get('surf_state_rules', {})
        single_max = rules.get('single_model', {}).get('max_uncertainty', 0.4)
        
        if ctx.uncertainty <= single_max:
            return SurfState.SINGLE_MODEL
        else:
            return SurfState.MULTI_MODEL

    def _log_decision(self, ctx: SurfingContext, dec: SurfingDecision):
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"decisions_{today}.csv"
        
        file_exists = log_file.exists()
        
        with open(log_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "timestamp", "regime", "uncertainty", "mode", "surf_state",
                    "risk_multiplier", "exit_aggressiveness", 
                    "allocation_kr", "allocation_us", "allocation_cash",
                    "recent_expectancy_R", "recent_drawdown_pct"
                ])
            
            writer.writerow([
                ctx.timestamp, ctx.regime.value, ctx.uncertainty, dec.mode.value, dec.surf_state.value,
                dec.risk_multiplier, dec.exit_aggressiveness,
                dec.allocation_kr, dec.allocation_us, dec.allocation_cash,
                ctx.recent_expectancy_R, ctx.recent_drawdown_pct
            ])
