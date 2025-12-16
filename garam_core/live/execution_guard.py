# garam_core/live/execution_guard.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ExecutionGuardParams:
    max_position_value_ratio: float = 0.30  # 계좌 대비 최대 30%
    market_close_block_min: int = 10        # 마감 10분 전 신규진입 차단
    max_order_notional: float = 50_000_000  # 주문당 최대 금액 (기본 5천만원)


def guard_position_size(
    equity: float,
    price: float,
    multiplier: float,
    params: ExecutionGuardParams,
) -> float:
    # 1. Total Position limit
    max_pos_value = equity * params.max_position_value_ratio
    
    # 2. Desired from Strategy
    desired_value = equity * multiplier
    
    # 3. Order Limit Capping (Logic is tricky here: desired_value is Target Position, not Order Size)
    # But usually this function is called for "New Entry" or "Rebalance".
    # Assuming this returns 'target_qty' or 'order_qty'? 
    # Context in live_runner: `qty = guard_position_size(...)` -> sent as BUY qty.
    # So this returns Order Qty?
    # No, `multiplier` is Target Leverage?
    # In `live_runner_stack.py`: `qty = guard_position_size(...)`.
    # `guard_position_size` calculates `return min(desired, max) / price`.
    # This implies it returns the TARGET POSITION size (if multiplier is passed).
    # IF it returns Target Qty, and current pos is 0, then Order Qty = Target Qty.
    # If partial pyrimiding... `multiplier` is usually `d.multiplier` (total).
    # Wait, `live_runner_stack` calls it for BUY.
    # If REBUY, it does `add_qty = guard(...) * d.qty_frac`.
    # So `guard` returns Full Target Size.
    
    # We should apply max_pos_value cap here.
    capped_value = min(desired_value, max_pos_value)
    
    # 4. Check against Order Limit?
    # If this is mapped to a SINGLE ORDER, we must verify if `capped_value` exceeds `max_order_notional`.
    # But `guard_position_size` returns a position sizing, not necessarily a single order.
    # However, for safety, we can cap the resulting value by `max_order_notional` IF logic assumes 1 order = 1 position entry.
    # In `live_runner`: `qty = guard(...)`. Then `router.send(qty)`.
    # So yes, result is converted to ONE order.
    # So we apply max_order_notional.
    capped_value = min(capped_value, params.max_order_notional)

    return capped_value / max(price, 1e-9)
