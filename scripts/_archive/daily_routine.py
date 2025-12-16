"""
Daily Routine Orchestrator
Runs the end-of-day process:
1. System Health Check
2. Data Fetch (Placeholder for 32-bit env)
3. Strategy Execution (Shadow Mode)
4. Report Generation

Usage: python scripts/daily_routine.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import yaml

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

def run_daily_routine():
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"[START] Starting Daily Routine: {datetime.now()}")
    
    # 0. Update Heartbeat
    health_dir = PATHS.LOGS_DIR / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    heartbeat_file = health_dir / "heartbeat.log"
    with open(heartbeat_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DAILY_ROUTINE] [START] [Starting Daily Cycle]\n")

    # 1. Health Check
    print("\n[1/4] [HEALTH] Checking System Health...")
    script_path = PATHS.SCRIPTS_DIR / "check_system_health.py"
    ret = os.system(f"python {script_path}")
    if ret != 0:
        print("[WARNING] Health Check Warning (Proceeding anyway)")

    # 2. Data Fetch
    print("\n[2/4] [DATA] Fetching Market Data...")
    script_path = PATHS.SCRIPTS_DIR / "fetch_daily_data_fdr.py"
    ret = os.system(f"python {script_path}")
    if ret != 0:
        print("[WARNING] Data Fetch Warning (Check logs)")

    # 3. Strategy Execution (Live Paper)
    print("\n[3/4] [EXEC] Running Strategy (Live Paper)...")
    script_path = PATHS.SCRIPTS_DIR / "run_live_trading.py"
    ret = os.system(f"python {script_path}")
    if ret != 0:
        print("[ERROR] Strategy Execution Failed!")
        return

    # Load Name Map
    name_map = {}
    try:
        with open(PATHS.CONFIG_DIR / "universe_kr_names.yaml", 'r', encoding='utf-8') as f:
            name_data = yaml.safe_load(f)
            name_map = name_data.get('symbols', {})
    except Exception as e:
        print(f"[WARNING] Could not load name map: {e}")

    # Load results for report
    shadow_results = {}
    try:
        with open(PATHS.STRATEGY_SIGNALS_LIVE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            shadow_results = {
                "date": data.get('date'),
                "signals": data.get('orders', []),
                "equity": data.get('equity', 0),
                "holdings": data.get('holdings', {}),
                "generated_at": data.get('generated_at', '')
            }
    except Exception as e:
        print(f"[WARNING] Could not load signals for report: {e}")
    
    # 3.5 Parse Risk Logs
    risk_warnings = []
    try:
        log_file = Path("paper_trading.log")
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='cp949') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()

            for line in lines:
                if today_str in line:
                    if "RISK BLOCK" in line:
                        # Extract message part: 2025-12-05 ... - WARNING - RISK BLOCK: 307950 BUY rejected. Reason: ...
                        parts = line.split("RISK BLOCK: ")
                        if len(parts) > 1:
                            detail = parts[1].strip()
                            # Detail ex: "307950 BUY rejected. Reason: Max Exposure Violation: Would be 135.1% (Limit: 100.0%)"
                            # Parse Symbol
                            sym_code = detail.split(' ')[0]
                            sym_name = name_map.get(sym_code, sym_code)
                            
                            # Parse Reason
                            reason_part = detail.split("Reason: ")[-1]
                            
                            risk_warnings.append({
                                "symbol": sym_code,
                                "name": sym_name,
                                "detail": detail,
                                "reason": reason_part
                            })
    except Exception as e:
        print(f"[WARNING] Error parsing risk logs: {e}")

    # 4. Generate Detailed Report
    print("\n[4/4] [REPORT] Generating Daily Report...")
    report_dir = PATHS.BASE_DIR / "reports"
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / f"Daily_Briefing_{today_str}.md"
    
    # Header
    markdown = f"""# � GARAM 일일 운용 브리핑 ({today_str})

안녕하세요, GARAM 자동매매 시스템입니다.
오늘의 운용 결과와 내일의 준비 상황을 보고드립니다.

## 1. � 요약 (Executive Summary)
- **운용 날짜**: {today_str}
- **포트폴리오 평가금**: **{shadow_results.get('equity', 0):,.0f} KRW**
- **시스템 상태**: ✅ 정상 가동 중
"""

    # 2. Strategy vs Execution
    markdown += """
## 2. 📈 금일 매매 분석 (Analysis)
오늘 시장 상황에 대응하여 시스템이 실행한 내역입니다.

### 전일 대비 특이사항
- 전일 계획된 전략과 실제 집행 내역의 차이를 분석합니다.
"""

    # Check for Blocked Orders (Difference)
    if risk_warnings:
        markdown += "- **⚠️ 주의**: 리스크 관리 모듈에 의해 일부 주문이 차단되었습니다(과도한 노출 방지 등).\n"
    else:
        markdown += "- 계획된 모든 신호가 정상적으로 집행되었습니다.\n"

    markdown += """
### 상세 거래 내역
| 종목명 (코드) | 주문 유형 | 수량 | 가격 | 상태 |
|:---|:---|:---|:---|:---|
"""
    # Combine Executed and Blocked
    # 1. Executed (from signals)
    for sig in shadow_results.get('signals', []):
        sym_code = sig.get('symbol')
        sym_name = name_map.get(sym_code, sym_code)
        action_kr = "매수" if sig.get('action') == 'BUY' else "매도"
        status_icon = "✅ 체결"
        markdown += f"| **{sym_name}** ({sym_code}) | {action_kr} | {sig.get('qty', 0):,}주 | {sig.get('price', 0):,.0f}원 | {status_icon} |\n"

    # 2. Blocked (from logs)
    for rw in risk_warnings:
        markdown += f"| **{rw['name']}** ({rw['symbol']}) | 매수 (차단됨) | - | - | ⛔ **차단** |\n"
        
    if not shadow_results.get('signals') and not risk_warnings:
        markdown += "| - | - | - | - | 매매 없음 |\n"

    # 3. Risk Detail
    if risk_warnings:
        markdown += """
### ⚠️ 리스크 한도 초과 상세 (Risk Violation Detail)
시스템 안정성을 위해 차단된 주문의 상세 사유입니다.

"""
        for rw in risk_warnings:
            markdown += f"- **{rw['name']} ({rw['symbol']})**\n"
            markdown += f"  - **차단 사유**: {rw['reason']}\n"
            # Try to parse "Would be X% (Limit: Y%)"
            # Expected format: "... Would be 135.1% (Limit: 100.0%)"
            import re
            m = re.search(r"Would be ([\d\.]+)% \(Limit: ([\d\.]+)%\)", rw['reason'])
            if m:
                curr_val = float(m.group(1))
                limit_val = float(m.group(2))
                excess = curr_val - limit_val
                markdown += f"  - **분석**: 허용 한도({limit_val}%)를 **{excess:.1f}% 초과** ({curr_val}%)하여 진입이 제한되었습니다.\n"
            markdown += "\n"

    # 4. Tomorrow's Plan (Holdings)
    markdown += """
## 3. 📅 내일의 준비 (Portfolio & Plan)
현재 보유 중인 포트폴리오 현황입니다. 내일 장 개시 전까지 이 구성을 유지합니다.

| 종목명 (코드) | 보유 수량 | 평단가 | 평가금액 |
|:---|:---|:---|:---|
"""
    holdings = shadow_results.get('holdings', {})
    if holdings:
        for sym, pos in holdings.items():
            sym_name = name_map.get(sym, sym)
            # Handle if pos is just list/dict
            qty = pos.get('qty', 0)
            avg_price = pos.get('entry_price', 0)
            val = pos.get('value', 0)
            markdown += f"| **{sym_name}** ({sym}) | {qty:,}주 | {avg_price:,.0f}원 | {val:,.0f}원 |\n"
    else:
        markdown += "| 보유 종목 없음 | - | - | - |\n"

    markdown += f"""
---
*보고서 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*GARAM Intelligent Trading System*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
        
    print(f"[DONE] Daily Routine Complete! Report saved to: {report_file}")

if __name__ == "__main__":
    run_daily_routine()
