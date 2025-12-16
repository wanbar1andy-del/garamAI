"""
Trade Comparator
Analyzes the gap between two sets of trades (Baseline vs Miracle).
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from garam.research.regime.miracle_engine import Trade

class TradeComparator:
    def __init__(self, baseline_trades: List[Trade], miracle_trades: List[Trade]):
        self.base = pd.DataFrame([t.__dict__ for t in baseline_trades])
        self.miracle = pd.DataFrame([t.__dict__ for t in miracle_trades])
        
        if not self.base.empty:
            self.base['entry_time'] = pd.to_datetime(self.base['entry_time'])
            self.base = self.base.sort_values('entry_time')
            
        if not self.miracle.empty:
            self.miracle['entry_time'] = pd.to_datetime(self.miracle['entry_time'])
            self.miracle = self.miracle.sort_values('entry_time')

    def match_trades(self, tolerance_days=5) -> pd.DataFrame:
        """
        Matches trades based on entry time and side.
        """
        if self.base.empty or self.miracle.empty:
            return pd.DataFrame()
            
        matches = []
        
        # Simple greedy matching
        # For each miracle trade, find closest base trade
        used_base_indices = set()
        
        for idx, m_trade in self.miracle.iterrows():
            # Filter base trades: same side, within time window
            candidates = self.base[
                (self.base['side'] == m_trade['side']) &
                (self.base['entry_time'] >= m_trade['entry_time'] - pd.Timedelta(days=tolerance_days)) &
                (self.base['entry_time'] <= m_trade['entry_time'] + pd.Timedelta(days=tolerance_days))
            ]
            
            best_match = None
            min_diff = pd.Timedelta(days=9999)
            
            for b_idx, b_trade in candidates.iterrows():
                if b_idx in used_base_indices: continue
                
                diff = abs(b_trade['entry_time'] - m_trade['entry_time'])
                if diff < min_diff:
                    min_diff = diff
                    best_match = b_idx
            
            if best_match is not None:
                used_base_indices.add(best_match)
                b_trade = self.base.loc[best_match]
                
                matches.append({
                    'miracle_entry': m_trade['entry_time'],
                    'base_entry': b_trade['entry_time'],
                    'entry_gap_days': (b_trade['entry_time'] - m_trade['entry_time']).days,
                    'miracle_pnl': m_trade['pnl_pct'],
                    'base_pnl': b_trade['pnl_pct'],
                    'pnl_gap': m_trade['pnl_pct'] - b_trade['pnl_pct'],
                    'miracle_exit_reason': m_trade['exit_reason'],
                    'base_exit_reason': b_trade['exit_reason'],
                    'regime': m_trade['regime']
                })
            else:
                # Unmatched Miracle Trade (Missed Opportunity)
                matches.append({
                    'miracle_entry': m_trade['entry_time'],
                    'base_entry': pd.NaT,
                    'entry_gap_days': np.nan,
                    'miracle_pnl': m_trade['pnl_pct'],
                    'base_pnl': 0.0,
                    'pnl_gap': m_trade['pnl_pct'],
                    'miracle_exit_reason': m_trade['exit_reason'],
                    'base_exit_reason': 'MISSED',
                    'regime': m_trade['regime']
                })
                
        return pd.DataFrame(matches)

    def generate_report(self) -> str:
        if self.base.empty: return "No baseline trades."
        if self.miracle.empty: return "No miracle trades."
        
        df = self.match_trades()
        if df.empty: return "No matches found."
        
        missed = df[df['base_exit_reason'] == 'MISSED']
        matched = df[df['base_exit_reason'] != 'MISSED']
        
        report = []
        report.append("## Gap Analysis Report")
        report.append(f"- Total Miracle Trades: {len(self.miracle)}")
        report.append(f"- Matched Trades: {len(matched)}")
        report.append(f"- Missed Opportunities: {len(missed)}")
        
        if not matched.empty:
            avg_gap = matched['pnl_gap'].mean()
            entry_lag = matched['entry_gap_days'].mean()
            report.append(f"- Avg PnL Gap (Miracle - Base): {avg_gap*100:.2f}%")
            report.append(f"- Avg Entry Lag (Base - Miracle): {entry_lag:.1f} days")
            
            # Analyze by Regime
            report.append("\n### By Regime")
            grp = matched.groupby('regime')[['pnl_gap', 'entry_gap_days']].mean()
            report.append(grp.to_string())
            
        if not missed.empty:
            missed_pnl = missed['miracle_pnl'].sum()
            baseline_pnl = self.base['pnl_pct'].sum() if not self.base.empty else 0.0
            
            report.append(f"\n### Missed Opportunities Impact")
            report.append(f"- Total Missed PnL: {missed_pnl*100:.2f}%")
            
            if baseline_pnl != 0:
                missed_ratio = missed_pnl / baseline_pnl
                report.append(f"- Missed Opp Ratio (Missed / Base): {missed_ratio*100:.2f}%")
            else:
                report.append(f"- Missed Opp Ratio: N/A (Baseline PnL is 0)")
            
        return "\n".join(report)
