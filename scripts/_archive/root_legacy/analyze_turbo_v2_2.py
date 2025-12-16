#!/usr/bin/env python3
"""
Turbo Overlay V2.2 시뮬레이션
V2.2: 매우 빠른 Exit (-1.5%)
"""

import pandas as pd
import numpy as np
from pathlib import Path

def calculate_mdd(equity_series):
    """MDD 계산"""
    cummax = equity_series.cummax()
    dd = (equity_series - cummax) / cummax
    return dd.min()

def calculate_concentration(positions_count):
    """포지션 수에 따른 집중도 추정"""
    if positions_count <= 0:
        return 0.0
    elif positions_count == 1:
        return 1.0
    elif positions_count == 2:
        return 1.0
    elif positions_count == 3:
        return 0.75
    elif positions_count == 4:
        return 0.65
    elif positions_count == 5:
        return 0.60
    else:
        return 0.50

def get_turbo_multiplier(concentration, max_mult=2.5):
    """집중도에 따른 Turbo multiplier"""
    min_concentration = 0.5
    
    if concentration < min_concentration:
        return 1.0
    
    multiplier = 1.0 + (max_mult - 1.0) * ((concentration - min_concentration) / (1.0 - min_concentration))
    
    return multiplier

def simulate_turbo_v2_2(df):
    """
    Turbo Overlay V2.2 시뮬레이션
    
    V2.2 개선 (매우 공격적):
    1. Exit: daily_return <= -1.5% 시 즉시 Turbo OFF (기존 -3%)
    2. Exit: 3일 합 <= -2.5% 시 Turbo OFF (기존 -4%)
    3. 재진입 조건: V2와 동일
    """
    df = df.copy()
    
    df['turbo_active_v2_2'] = False
    df['concentration'] = 0.0
    df['turbo_multiplier_v2_2'] = 1.0
    df['turbo_equity_v2_2'] = df['equity'].copy()
    df['exit_reason_v2_2'] = ''
    df['reentry_reason_v2_2'] = ''
    
    equity = 100_000_000
    is_turbo_active = False
    turbo_off_date = None
    turbo_off_dd = 0
    turbo_off_equity = equity
    portfolio_high = equity
    
    recent_returns = []
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        date = row['date']
        
        concentration = calculate_concentration(row['positions_count'])
        df.loc[df.index[idx], 'concentration'] = concentration
        
        recent_returns.append(row['daily_return'])
        if len(recent_returns) > 3:
            recent_returns.pop(0)
        
        regime_ok = True
        can_activate_turbo = regime_ok and concentration >= 0.5
        
        # === V2.2 EXIT 조건 (매우 빠름!) ===
        if is_turbo_active:
            multiplier = get_turbo_multiplier(concentration)
            
            # Exit 조건 1: 단일일 급락 -1.5% (V2: -3%)
            if multiplier >= 2.0 and row['daily_return'] <= -0.015:
                is_turbo_active = False
                turbo_off_date = date
                turbo_off_equity = equity
                turbo_off_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                df.loc[df.index[idx], 'exit_reason_v2_2'] = f'Daily drop {row["daily_return"]*100:.1f}%'
                multiplier = 1.0
            
            # Exit 조건 2: 연속 하락 (3일 합 <= -2.5%) (V2: -4%)
            elif multiplier >= 2.0 and len(recent_returns) >= 3:
                sum_3d = sum(recent_returns)
                if sum_3d <= -0.025:
                    is_turbo_active = False
                    turbo_off_date = date
                    turbo_off_equity = equity
                    turbo_off_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                    df.loc[df.index[idx], 'exit_reason_v2_2'] = f'3-day decline {sum_3d*100:.1f}%'
                    multiplier = 1.0
        
        # === V2.2 재진입 조건 (V2와 동일) ===
        if not is_turbo_active and can_activate_turbo:
            if turbo_off_date is not None:
                days_since_exit = (pd.to_datetime(date) - pd.to_datetime(turbo_off_date)).days
                
                if days_since_exit >= 3:
                    current_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                    
                    if turbo_off_dd < 0:
                        recovery_ratio = 1 - (current_dd / turbo_off_dd)
                    else:
                        recovery_ratio = 1.0
                    
                    recent_sum = sum(recent_returns[-2:]) if len(recent_returns) >= 2 else 0
                    momentum_ok = (recent_sum >= 0.03) or (row['daily_return'] >= 0.02)
                    
                    concentration_ok = concentration >= 0.8
                    
                    if recovery_ratio >= 0.5 and momentum_ok and concentration_ok:
                        is_turbo_active = True
                        df.loc[df.index[idx], 'reentry_reason_v2_2'] = f'Recovery {recovery_ratio*100:.0f}%, Mom {recent_sum*100:.1f}%'
            else:
                if concentration >= 0.8:
                    is_turbo_active = True
                    df.loc[df.index[idx], 'reentry_reason_v2_2'] = 'Initial entry'
        
        # Multiplier 계산
        if is_turbo_active and can_activate_turbo:
            multiplier = get_turbo_multiplier(concentration)
        else:
            multiplier = 1.0
        
        df.loc[df.index[idx], 'turbo_active_v2_2'] = is_turbo_active
        df.loc[df.index[idx], 'turbo_multiplier_v2_2'] = multiplier
        
        # Equity 계산
        turbo_return = row['daily_return'] * multiplier
        equity = equity * (1 + turbo_return)
        
        if equity > portfolio_high:
            portfolio_high = equity
        
        df.loc[df.index[idx], 'turbo_equity_v2_2'] = equity
    
    return df

if __name__ == "__main__":
    print("V2.2 시뮬레이션 모듈 로드 완료")
