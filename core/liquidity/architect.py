
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AccountNode:
    id: str
    owner: str
    capital: float
    allocation: float = 0.0 # Current position
    
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
    Control Tower for Multi-Account Liquidity Management.
    Calculates Market Impact and separates 'Alpha' (Market) from 'Impact' (Self).
    """
    def __init__(self):
        self.accounts: Dict[str, AccountNode] = {}
        self.active_orders: Dict[str, float] = {} 
        # Learnable Impact Coefficient (k)
        # Starting point: 0.8 (Aggressive)
        self.impact_k = 0.8 
        self.learning_rate = 0.05
        
    def add_account(self, id: str, owner: str, capital: float):
        self.accounts[id] = AccountNode(id, owner, capital)
        
    def aggregate_firepower(self, target_symbol: str) -> float:
        total_qty = sum(self.active_orders.values())
        return total_qty

    def estimate_impact(self, qty: float, market_vol: float, volatility: float, price: float) -> float:
        if market_vol == 0: return 0.0
        
        participation = qty / market_vol
        # Use learned k
        impact_pct = self.impact_k * volatility * np.sqrt(participation)
        impact_price = price * impact_pct
        return impact_price

    def learn_from_execution(self, executed_qty, expected_price, actual_avg_price, market_vol, volatility):
        """
        [Active Learning]
        Compare estimated slippage vs actual slippage.
        Adjust 'k' to match reality.
        """
        real_slippage_pct = abs(actual_avg_price - expected_price) / expected_price
        
        # Reverse engineer what 'k' should have been
        # slippage = k * vol * sqrt(participation)
        # k = slippage / (vol * sqrt(part))
        participation = executed_qty / market_vol
        denominator = volatility * np.sqrt(participation)
        if denominator == 0: return
        
        target_k = real_slippage_pct / denominator
        
        # Update k (Moving Average)
        old_k = self.impact_k
        self.impact_k = old_k * (1 - self.learning_rate) + target_k * self.learning_rate
        
        print(f"   [LEARNING] Impact Model Adjusted: k={old_k:.3f} -> {self.impact_k:.3f}")
        if target_k > old_k:
            print("   -> Market is THINNER than expected. (Increased Impact Estimate)")
        else:
            print("   -> Market is DEEPER than expected. (Decreased Impact Estimate)")
        
    def analyze_move(self, start_price, end_price, qty, market_vol, volatility):
        """
        Decompose the price move into:
        1. Self-Induced Impact (We pushed it)
        2. Pure Market Momentum (Market pushed it)
        """
        actual_move = end_price - start_price
        induced_move = self.estimate_impact(qty, market_vol, volatility, start_price)
        
        pure_move = actual_move - induced_move
        
        # Signal: Exit if Pure Move is fading but we are still pushing
        signal = "HOLD"
        if pure_move < 0 and induced_move > 0:
            signal = "EXIT_NOW (No Real Demand)"
        elif pure_move > induced_move:
            signal = "ADD (Strong Real Demand)"
            
        return {
            "actual_move": actual_move,
            "induced_move": induced_move,
            "pure_move": pure_move,
            "signal": signal
        }

    def generate_impact_report(self, history: List[dict]):
        print("\n" + "="*60)
        print("          GARAM LIQUIDITY ARCHITECT: IMPACT REPORT          ")
        print("="*60)
        
        # Aggregation
        df = pd.DataFrame(history)
        
        total_pnl = df['actual_move'].sum()
        self_pnl = df['induced_move'].sum()
        market_pnl = df['pure_move'].sum()
        
        print(f"1. [Aggregated Firepower]")
        print(f"   Total Accounts: {len(self.accounts)}")
        print(f"   Total Cap: ₩{sum(a.capital for a in self.accounts.values()):,.0f}")
        print("-" * 30)
        
        print(f"2. [Attribution Analysis]")
        print(f"   Total Price Rise: {total_pnl:+,.0f} KRW")
        print(f"   ├── 🔴 Self-Induced: {self_pnl:+,.0f} KRW ({(self_pnl/total_pnl)*100:.1f}%) -> 'Bubble we made'")
        print(f"   └── 🟢 Pure Market : {market_pnl:+,.0f} KRW ({(market_pnl/total_pnl)*100:.1f}%) -> 'Real Value'")
        
        print("\n3. [Tactical Insight]")
        if self_pnl > market_pnl:
            print("   ⚠️ WARNING: Price rise is mostly artificial.")
            print("   ACTION: Execute Impact-Free Unloading (TWAP/VWAP).")
        else:
            print("   ✅ CONFIRM: Market is organically strong.")
            print("   ACTION: Hold for target.")
            
        print("="*60 + "\n")

if __name__ == "__main__":
    # Test Simulation
    arch = LiquidityArchitect()
    arch.add_account("ACC_MAIN", "JS.JUNG", 100_000_000)
    arch.add_account("ACC_FAM1", "Family A", 50_000_000)
    arch.add_account("ACC_FAM2", "Family B", 30_000_000)
    
    # Scenario: We buy 10,000 shares of Samsung Elec
    # Daily Vol: 10M, Volatility: 2%
    # Price moves from 70,000 -> 72,000
    
    print("\n>> Simulating Order Execution...")
    history = []
    price = 70000
    vol = 0.02
    mkt_vol = 5_000_000 # 5M shares
    
    # We push 50,000 shares (Big aggregation)
    my_qty = 50000 
    
    # Market reacts
    final_price = 72000 # Rose 2000 won
    
    analysis = arch.analyze_move(price, final_price, my_qty, mkt_vol, vol)
    history.append(analysis)
    
    arch.generate_impact_report(history)
.
