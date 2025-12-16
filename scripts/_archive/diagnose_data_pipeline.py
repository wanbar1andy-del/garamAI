#!/usr/bin/env python3
"""
Data Pipeline Diagnostics
Universe → Score → Signals 간 일관성 검증
"""
import pandas as pd
import json
import yaml
from pathlib import Path
from datetime import datetime
import sys

def diagnose_pipeline(universe_file, score_file, signals_file=None, date=None):
    """
    데이터 파이프라인 정합성 진단
    
    Args:
        universe_file: 유니버스 CSV 경로
        score_file: 스코어 CSV 경로  
        signals_file: signals_live.json 경로 (옵션)
        date: 체크할 날짜 (옵션, 기본: 최신)
    
    Returns:
        bool: 모든 체크 통과 여부
    """
    print(f"\n{'='*70}")
    print(f"GARAM Data Pipeline Diagnostics - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    
    issues = []
    
    # 1. Load Universe
    print(f"[1/4] Loading Universe: {universe_file}")
    try:
        df_universe = pd.read_csv(universe_file)
        
        if 'symbol' in df_universe.columns:
            universe_symbols = set(df_universe['symbol'].astype(str))
        elif 'Code' in df_universe.columns:
            universe_symbols = set(df_universe['Code'].astype(str))
        else:
            universe_symbols = set(df_universe.iloc[:, 0].astype(str))
        
        print(f"  ✓ Universe loaded: {len(universe_symbols)} symbols")
    except Exception as e:
        print(f"  ❌ Failed to load universe: {e}")
        return False
    
    # 2. Load Scores
    print(f"\n[2/4] Loading Scores: {score_file}")
    try:
        df_scores = pd.read_csv(score_file)
        df_scores['date'] = pd.to_datetime(df_scores['date'])
        
        latest_date = df_scores['date'].max() if date is None else pd.to_datetime(date)
        age_days = (pd.Timestamp.now() - latest_date).days
        
        print(f"  ✓ Score file date range: {df_scores['date'].min().date()} ~ {latest_date.date()}")
        print(f"  ⏱️  Age: {age_days} days")
        
        if age_days > 3:
            print(f"  ⚠️  WARNING: Score file is {age_days} days old!")
            issues.append(f"Score file is {age_days} days old (threshold: 3)")
        
        # Latest scores
        df_latest = df_scores[df_scores['date'] == latest_date]
        score_symbols = set(df_latest['symbol'].astype(str))
        
        print(f"  ✓ Symbols with scores on {latest_date.date()}: {len(score_symbols)}")
    except Exception as e:
        print(f"  ❌ Failed to load scores: {e}")
        return False
    
    # 3. Compare Universe vs Scores
    print(f"\n[3/4] Comparing Universe ↔ Scores")
    
    missing_in_scores = universe_symbols - score_symbols
    extra_in_scores = score_symbols - universe_symbols
    common = universe_symbols & score_symbols
    
    coverage = len(common) / len(universe_symbols) if universe_symbols else 0
    
    print(f"  Common symbols:     {len(common):>4} ({coverage:>5.1%})")
    print(f"  Missing in scores:  {len(missing_in_scores):>4}")
    print(f"  Extra in scores:    {len(extra_in_scores):>4}")
    
    if missing_in_scores:
        print(f"\n  ⚠️  Missing in scores (first 30):")
        for sym in sorted(list(missing_in_scores))[:30]:
            print(f"    - {sym}")
    
    if extra_in_scores:
        print(f"\n  ℹ️  Extra in scores (first 20):")
        for sym in sorted(list(extra_in_scores))[:20]:
            print(f"    - {sym}")
    
    if len(missing_in_scores) > len(universe_symbols) * 0.1:
        issues.append(f"{len(missing_in_scores)} symbols missing in scores (>{10}%)")
    
    # 4. Check Signals (if provided)
    if signals_file and Path(signals_file).exists():
        print(f"\n[4/4] Checking Signals: {signals_file}")
        
        try:
            with open(signals_file) as f:
                signals = json.load(f)
            
            signals_date = signals.get('date', 'unknown')
            holdings = signals.get('holdings', {})
            signal_symbols = set(holdings.keys())
            
            print(f"  ✓ Signals date: {signals_date}")
            print(f"  ✓ Holdings: {len(signal_symbols)} symbols")
            
            # Check if holdings have scores
            holdings_no_score = signal_symbols - score_symbols
            
            if holdings_no_score:
                print(f"\n  ❌ CRITICAL: Holdings WITHOUT scores:")
                for sym in sorted(holdings_no_score):
                    print(f"    - {sym}")
                issues.append(f"{len(holdings_no_score)} held positions without scores")
            else:
                print(f"  ✓ All holdings have scores")
        except Exception as e:
            print(f"  ⚠️  Failed to check signals: {e}")
    else:
        print(f"\n[4/4] Signals file not provided or not found")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    
    if issues:
        print(f"\n❌ ISSUES FOUND ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        # Save issues to log
        log_path = Path('logs/data_pipeline_alerts.log')
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{datetime.now()}\n")
            for issue in issues:
                f.write(f"  - {issue}\n")
        
        return False
    else:
        print(f"\n✅ All checks passed!")
        print(f"  - Coverage: {coverage:.1%}")
        print(f"  - Score freshness: {age_days} days")
        print(f"  - No holdings without scores")
        return True

if __name__ == "__main__":
    universe = "GARAM_Data/real_universe_400.csv"
    scores = "GARAM_Data/real_scores_2024.csv"
    signals = "GARAM_Data/strategy/signals_live.json"
    
    if len(sys.argv) > 1:
        universe = sys.argv[1]
    if len(sys.argv) > 2:
        scores = sys.argv[2]
    if len(sys.argv) > 3:
        signals = sys.argv[3]
    
    success = diagnose_pipeline(universe, scores, signals)
    sys.exit(0 if success else 1)
