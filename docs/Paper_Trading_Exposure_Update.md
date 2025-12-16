# Paper Trading 로그 포맷 업데이트 가이드

**날짜**: 2025-11-26  
**목적**: Paper Trading 로그에 노출(Exposure) 정보 추가

---

## 🎯 필요한 정보

현재 Paper Trading 로그( `trades_{YYYYMMDD}.json`)에 다음 필드를 추가해야 합니다:

### 거래 레벨 (Trade-level)

```json
{
  "timestamp": "2025-11-26T10:30:15",
  "symbol": "005930",
  "side": "BUY",
  "price": 70500,
  "quantity": 100,
  "realized_pnl": 150000,
  
  // 추가 필요
  "exposure_pct": 0.05,  // 이 포지션의 노출 (5%)
  "portfolio_exposure_pct": 0.32,  // 거래 후 포트폴리오 전체 노출 (32%)
  "position_value": 7050000,  // 포지션 가치 (price * quantity)
  "portfolio_value": 105000000  // 거래 시점 포트폴리오 가치
}
```

### 일일 요약 (Daily Summary)

```json
{
  "date": "20251126",
  "trades": [...],
  
  // 추가 필요
  "daily_summary": {
    "avg_gross_exposure_pct": 28.5,  // 일평균 노출
    "max_gross_exposure_pct": 45.2,  // 최대 노출
    "min_gross_exposure_pct": 12.3,  // 최소 노출
    "avg_position_count": 4.2,  // 평균 동시 포지션 수
    "max_position_count": 7,  // 최대 동시 포지션 수
    "capital_efficiency": 2.8  // (선택) CAGR / Avg Exposure (추정치)
  }
}
```

---

## 📝 구현 가이드

### 1. ShadowTrader 또는 Paper Trading Engine에서 추가

구현 위치: `garam/live/shadow_trader.py` 또는 해당 모듈

```python
class ShadowTrader:
    def __init__(self):
        self.portfolio_value = 100_000_000  # Initial
        self.positions = {}  # {symbol: {quantity, avg_price, ...}}
        
    def calculate_exposure(self):
        """Calculate current gross exposure"""
        total_position_value = sum(
            abs(pos['quantity'] * pos['current_price']) 
            for pos in self.positions.values()
        )
        
        gross_exposure_pct = total_position_value / self.portfolio_value
        
        return gross_exposure_pct
    
    def on_trade(self, trade):
        """Record trade with exposure info"""
        # Update positions
        self._update_positions(trade)
        
        # Calculate current exposure
        portfolio_exposure = self.calculate_exposure()
        
        # Add to trade log
        trade_log = {
            'timestamp': trade['timestamp'],
            'symbol': trade['symbol'],
            'side': trade['side'],
            'price': trade['price'],
            'quantity': trade['quantity'],
            'realized_pnl': trade.get('realized_pnl', 0),
            
            # New fields
            'position_value': abs(trade['price'] * trade['quantity']),
            'exposure_pct': abs(trade['price'] * trade['quantity']) / self.portfolio_value,
            'portfolio_exposure_pct': portfolio_exposure,
            'portfolio_value': self.portfolio_value
        }
        
        self.trades.append(trade_log)
        
        return trade_log
    
    def get_daily_summary(self):
        """Calculate daily exposure summary"""
        if not self.exposure_history:
            return {}
        
        return {
            'avg_gross_exposure_pct': np.mean(self.exposure_history) * 100,
            'max_gross_exposure_pct': np.max(self.exposure_history) * 100,
            'min_gross_exposure_pct': np.min(self.exposure_history) * 100,
            'avg_position_count': np.mean(self.position_count_history),
            'max_position_count': np.max(self.position_count_history)
        }
```

### 2. 로그 저장 시 포함

```python
def save_daily_trades(date_str, trades, summary):
    """Save trades with exposure data"""
    log_file = PATHS.DATA_ROOT / "kr" / "paper_trading" / f"trades_{date_str}.json"
    
    data = {
        'date': date_str,
        'trades': trades,
        'daily_summary': summary  # 추가
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## ✅ 검증 방법

### 1. 로그 파일 확인

```bash
# 오늘 로그 파일 확인
cat "g:/내 드라이브/garamdata/kr/paper_trading/trades_20251126.json"
```

예상 출력:

```json
{
  "date": "20251126",
  "trades": [
    {
      "timestamp": "2025-11-26T09:35:00",
      "symbol": "005930",
      "exposure_pct": 0.05,
      "portfolio_exposure_pct": 0.32,
      ...
    }
  ],
  "daily_summary": {
    "avg_gross_exposure_pct": 28.5,
    "max_gross_exposure_pct": 45.2
  }
}
```

### 2. 분석 스크립트 테스트

```bash
# Paper Trading 분석 스크립트 실행
python scripts/analyze_paper_trading_logs.py --date today
```

출력에서 노출 정보 확인:

```
📊 Capital Utilization
   Avg Gross Exposure: 28.5%
   Max Gross Exposure: 45.2%
   Avg Positions: 4.2
```

### 3. Portfolio Efficiency 분석

```bash
# 일주일치 데이터로 Capital Efficiency 계산
python scripts/analyze_portfolio_efficiency.py \
    --paper-trading \
    --date-range 20251120-20251126
```

예상 출력:

```
⚡ Capital Efficiency: 2.8
   Rating: ✅ Good
   Action: MAINTAIN - Current allocation is optimal
```

---

## 🔧 Troubleshooting

### 문제 1: exposure_pct 필드가 없음

**원인**: 기존 로그 파일에는 해당 필드 없음

**해결**:

1. 새로운 로그 파일부터 적용 (오늘부터)
2. 또는 fallback 로직 추가:

   ```python
   if 'exposure_pct' in trade:
       exposure = trade['exposure_pct']
   else:
       # Estimate from trade value
       exposure = (trade['price'] * trade['quantity']) / portfolio_value
   ```

### 문제 2: Portfolio value 추적 오류

**원인**: 포트폴리오 가치가 고정값으로 설정됨

**해결**:

- PnL을 누적하여 portfolio_value 업데이트:

  ```python
  self.portfolio_value += realized_pnl
  ```

### 문제 3: 일일 요약 계산 안 됨

**원인**: exposure_history가 비어 있음

**해결**:

- 매 거래마다 exposure를 history에 추가:

  ```python
  self.exposure_history.append(self.calculate_exposure())
  ```

---

## 📅 구현 우선순위

### Priority 1 (즉시)

- [x] `exposure_pct` 필드 추가
- [x] `portfolio_exposure_pct` 필드 추가
- [x] `position_value` 필드 추가

### Priority 2 (이번 주)

- [ ] `daily_summary` 섹션 추가
- [ ] `avg_gross_exposure_pct` 계산
- [ ] `analyze_portfolio_efficiency.py`와 연동 테스트

### Priority 3 (다음 주)

- [ ] 실시간 노출 모니터링 대시보드 (GaramUI)
- [ ] 노출 상한선 알림 (80% 초과 시)
- [ ] Capital Efficiency 주간 리포트 자동 생성

---

## 🔗 관련 파일

- Paper Trading Engine: `garam/live/shadow_trader.py` (추정)
- 로그 분석: [`scripts/analyze_paper_trading_logs.py`](file:///c:/garam/garam/scripts/analyze_paper_trading_logs.py)
- Efficiency 분석: [`scripts/analyze_portfolio_efficiency.py`](file:///c:/garam/garam/scripts/analyze_portfolio_efficiency.py)
- KPI 정의: [`docs/DGE_Portfolio_KPI.md`](file:///c:/garam/garam/docs/DGE_Portfolio_KPI.md)

---

## ✅ 완료 체크리스트

- [ ] ShadowTrader에 exposure 계산 로직 추가
- [ ] Trade 로그에 exposure_pct, portfolio_exposure_pct 필드 추가
- [ ] Daily summary 섹션 추가
- [ ] analyze_paper_trading_logs.py에서 노출 정보 출력 확인
- [ ] analyze_portfolio_efficiency.py로 Capital Efficiency 계산 테스트
- [ ] 1주일 데이터로 실제 metrics 검증
