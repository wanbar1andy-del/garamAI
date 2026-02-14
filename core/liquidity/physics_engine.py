
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict
from core.active_config.tactical_genome import dna

@dataclass
class AccountNode:
    id: str
    owner: str
    capital: float
    allocation: float = 0.0
    
@dataclass
class LiquidityMetrics:
    total_order_size: float
    market_volume: float
    volatility: float
    
    @property
    def participation_rate(self):
        return self.total_order_size / (self.market_volume + 1e-9)

class LiquidityArchitect:
    """
    Control Tower, Physics Engine.
    Renamed/Refactored to ensure clean state.
    """
    def __init__(self):
        self.accounts: Dict[str, AccountNode] = {}
        self.active_orders: Dict[str, float] = {} 
        self.impact_k = 0.8 
        self.learning_rate = 0.05
    
    def calculate_fitness(self, profit, risk, complexity):
        """
        [Evolutionary Fitness Function]
        Fitness = Profit / (Risk * Complexity)
        """
        if risk * complexity == 0: return 0
        return profit / (risk * complexity)

    def calculate_typhoon_probability(self, market_total_val, sector_val):
        base_score = 50.0
        market_boost = min(30.0, (market_total_val / 10_000_000_000_000) * 20.0)
        return base_score + market_boost

    def calculate_impact_power(self, capital: float, adv: float, volatility: float) -> dict:
        if adv <= 0 or volatility <= 0:
            return {"power_score": 999.0, "status": "DANGER", "slicing": "NONE"}
        
        raw_power = capital / (adv * volatility)
        min_p = dna.get("impact_power_min")
        max_p = dna.get("impact_power_max")
        danger_p = 0.15 
        
        status = "UNKNOWN"
        slicing = "STANDARD"
        
        if raw_power > danger_p:
            status = "DANGER"
            slicing = "ABORT"
        elif max_p < raw_power <= danger_p:
            status = "AGGRESSIVE"
            slicing = "SLICE_50"
        elif min_p <= raw_power <= max_p:
            status = "OPTIMAL"
            slicing = "SLICE_10"
        else:
            status = "NEGLIGIBLE"
            slicing = "IMMEDIATE"
            
        return {"power_score": raw_power * 100, "status": status, "slicing": slicing}

    def add_account(self, id: str, owner: str, capital: float):
        self.accounts[id] = AccountNode(id, owner, capital)
        
    def aggregate_firepower(self, target_symbol: str) -> float:
        return sum(self.active_orders.values())

    def estimate_impact(self, qty: float, market_vol: float, volatility: float, price: float) -> float:
        if market_vol == 0: return 0.0
        participation = qty / market_vol
        impact_pct = self.impact_k * volatility * np.sqrt(participation)
        return price * impact_pct

    def learn_from_execution(self, executed_qty, expected_price, actual_avg_price, market_vol, volatility):
        real_slippage_pct = abs(actual_avg_price - expected_price) / expected_price
        participation = executed_qty / market_vol
        denominator = volatility * np.sqrt(participation)
        if denominator == 0: return
        target_k = real_slippage_pct / denominator
        self.impact_k = self.impact_k * (1 - self.learning_rate) + target_k * self.learning_rate

    def analyze_move(self, start_price, end_price, qty, market_vol, volatility):
        actual_move = end_price - start_price
        induced_move = self.estimate_impact(qty, market_vol, volatility, start_price)
        pure_move = actual_move - induced_move
        signal = "HOLD"
        if pure_move < 0 and induced_move > 0: signal = "EXIT_NOW"
        elif pure_move > induced_move: signal = "ADD"
        return {"actual_move": actual_move, "induced_move": induced_move, "pure_move": pure_move, "signal": signal}
