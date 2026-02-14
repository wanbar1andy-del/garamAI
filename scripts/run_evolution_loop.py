
"""
GARAM Evolutionary Loop (OSS Level 3)
--------------------------------------
The Missing Link: Data -> Feedback -> Action -> Evolution

기능:
1. Tactical Log (Ghost Tail) 분석
2. 시스템 편향(Bias) 진단 (너무 빨리 파는지, 너무 늦게 파는지)
3. 진화 제안(Evolution Proposal) 생성 -> antigravity_feedback.md
4. 자동 파라미터 튜닝 제안
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"
REPORT_DIR = PROJECT_ROOT / "reports"
FEEDBACK_FILE = REPORT_DIR / "antigravity_feedback.md"

def load_ghost_logs():
    """Load aggregated ghost tail logs"""
    path = LOG_DIR / "ghost_tail.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def analyze_bias(df: pd.DataFrame):
    """
    진단: 우리의 매매 습관은 어떠한가?
    Ghost Return (120m) > 0: 내가 판 것보다 올랐다 (Too Early Exit)
    Ghost Return (120m) < 0: 내가 판 것보다 내렸다 (Good Exit)
    """
    if df.empty:
        return {"status": "INSUFFICIENT_DATA"}
        
    total = len(df)
    # 0.5% Threshold
    too_early = len(df[df['diff_120m'] > 0.5])
    good_exit = len(df[df['diff_120m'] < -0.5])
    neutral = total - too_early - good_exit
    
    early_ratio = too_early / total
    good_ratio = good_exit / total
    
    # Diagnosis
    bias = "BALANCED"
    severity = 0.0
    
    if early_ratio > 0.6:
        bias = "VIGILANT_FEAR" # 너무 겁이 많음 (빨리 팖)
        severity = (early_ratio - 0.6) * 2.5 # 0 ~ 1.0 scale
    elif good_ratio > 0.6:
        bias = "PRECISE_SNIPER" # 매우 정확함 (유지 추천)
        severity = 0.0
    elif (total > 10) and (good_ratio < 0.2) and (early_ratio < 0.2):
         bias = "NOISE_TRADER" # 아무 의미 없는 매매
         
    return {
        "status": "ACTIVE",
        "total_trades": total,
        "bias": bias,
        "early_ratio": early_ratio,
        "good_ratio": good_ratio,
        "severity": severity,
        "avg_opportunity_loss": df[df['diff_120m']>0]['diff_120m'].mean() if too_early > 0 else 0.0
    }

def generate_evolution_proposal(diagnosis: dict):
    """진화 제안 생성"""
    if diagnosis["status"] != "ACTIVE":
        return None
        
    bias = diagnosis["bias"]
    severity = diagnosis["severity"]
    
    proposal = {
        "timestamp": datetime.now().isoformat(),
        "diagnosis": f"Detected Bias: {bias} (Severity: {severity:.2f})",
        "action_items": []
    }
    
    if bias == "VIGILANT_FEAR":
        # Action: Loosen Profit Taking / Trailing Stop
        proposal["action_items"].append({
            "component": "EXIT_LOGIC",
            "parameter": "trailing_stop_buffer",
            "direction": "INCREASE",
            "reason": f"System exits too early ({diagnosis['early_ratio']*100:.1f}%). Market often rises after we sell."
        })
        proposal["action_items"].append({
            "component": "MENTAL",
            "parameter": "patience",
            "direction": "BOOST",
            "reason": f"Avg Opportunity Loss: {diagnosis['avg_opportunity_loss']:.2f}%"
        })
    elif bias == "PRECISE_SNIPER":
        proposal["action_items"].append({
            "component": "CAPITAL",
            "parameter": "position_sizing",
            "direction": "INCREASE",
            "reason": "Exit timing is highly accurate. Safe to increase bet size."
        })
        
    return proposal

def write_antigravity_feedback(proposal):
    """안티그레비티에게 보낼 피드백 파일 작성"""
    if not proposal:
        text = "No sufficient data for evolution yet."
    else:
        text = f"# 🧬 Garam Evolutionary Feedback\n\n"
        text += f"**Timestamp**: {proposal['timestamp']}\n\n"
        text += f"## 🔍 Diagnosis\n"
        text += f"- **Result**: {proposal['diagnosis']}\n\n"
        text += f"## 🚀 Evolution Proposals\n"
        for item in proposal['action_items']:
            text += f"### {item['component']} -> {item['direction']}\n"
            text += f"- **Target**: `{item['parameter']}`\n"
            text += f"- **Logic**: {item['reason']}\n\n"
            
        text += "---\n"
        text += "**User Instruction**: Please review this feedback and apply changes to the engine if agreed.\n"
        
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"[Evolution] Feedback loops connected. Proposal saved to {FEEDBACK_FILE}")

def main():
    print("=== Garam Evolutionary Loop (Level 3) ===")
    
    # 1. Load Last Tactical Data
    df = load_ghost_logs()
    print(f"Loaded {len(df)} ghost tail records.")
    
    # 2. Diagnose
    diagnosis = analyze_bias(df)
    print(f"Diagnosis: {diagnosis}")
    
    # 3. Propose Evolution
    proposal = generate_evolution_proposal(diagnosis)
    
    # 4. Feedback to Antigravity (File System)
    write_antigravity_feedback(proposal)

if __name__ == "__main__":
    main()
