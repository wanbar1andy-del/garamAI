# SSOT Signal Mining Contract v1.0

- 문서명: SSOT_Signal_Mining_Contract_v1_0.md
- 버전: 1.0
- 최종수정: 2025-12-20
- 목적: Hero 구간의 시작(Birth)과 끝(Death)을 사전에 포착할 수 있는 선행 지표(Leading Indicator)를 발굴한다.

---

## 0. 전제 및 연결 문서 (Dependencies)

- 본 계약은 **SSOT Trade Execution Audit Contract v1.0**(Gate A/B/C)을 상위 통제로 상정한다.
- 본 계약 산출물은 Policy v1 후보 생성에 사용되며, 최종 검증은 반드시 Audit Contract 기준으로 재현되어야 한다.
- 기준치(Oracle Upper Bound): **100% 최적화 시 +31.29% (1일)** (참고용 상한선)

---

## 1. 마이닝 대상 정의 (Targets)

### Target A: Birth (진입 시그널)

- **정의**: "의미 있는 Hero Segment"가 시작되기 직전 $T_{start} - k$분 구간.
- **Goal**: 남들이 1등임을 알아채기 전에(Rank < 10일 때) 진입하여 초기 상승분을 확보.
- **성공 기준**:
  - Precision > 60% (진입 시 10분 내 Top-3 진입 확률)
  - Lead Time $\ge$ 1분

### Target B: Death (청산 시그널)

- **정의**: Hero Segment가 종료($T_{end}$)되기 직전 $T_{end} - k$분 구간.
- **Goal**: 랭크나 수익률이 꺾이기 전에(Reaction Time > 0) 선제 매도.
- **성공 기준**:
  - Recall > 80% (폭락 전 탈출 성공률)
  - Reaction Time > 0분 (평균)

---

## 2. 후보 피처 (Candidate Features)

### 2.1 랭크 기반 (Rank Dynamics)

- `Rank_Velocity`: 랭크 상승 속도 (예: 1분 전 20위 $\to$ 현재 5위)
- `Rank_Stability`: 상위권 유지 시간 (잔파동 필터링)

### 2.2 거래량 기반 (Volume Dynamics)

- `Vol_Accel`: 직전 N분 평균 대비 현재 거래량 급증 (Volume Spike)
- `Vol_Concentration`: 전체 시장 거래대금 중 해당 종목 비중 변화

### 2.3 가격/모멘텀 기반 (Price/Momentum)

- `VWAP_Div`: 현재가와 당일 VWAP 간 이격도 (확대 $\to$ 과열, 축소 $\to$ 눌림목)
- `ROC_5m`: 5분 수익률(모멘텀) 변화율
- `Program_Flow`: 프로그램 순매수 가속 (가능한 경우)

---

## 3. 마이닝 방법론 (Methodology)

### 3.1 Supervised Learning Dataset 구축

- **Positive Samples**:
  - Birth: $T_{start}$ 전후 5분(또는 $T_{start}-k$ 중심의 윈도우)
  - Death: $T_{end}$ 전후 5분(또는 $T_{end}-k$ 중심의 윈도우)
- **Negative Samples**:
  - Birth: $T_{start}$와 충분히 떨어진 동일 종목의 랜덤 구간(예: -30분)
  - Death: 세그먼트 중간(Mid) 구간(Exit가 일어나면 안 되는 구간)

### 3.2 평가 지표 (Evaluation Metrics)

1. **Information Value (IV)**: 피처가 Target을 얼마나 잘 분리하는가?
2. **Conditional Probability $P(Hero|Signal)$**: 신호 발생 시 실제 히어로가 될 확률.
3. **Regret Reduction**: 해당 신호 사용 시 `Week-1 Audit`의 Regret이 감소하는가?
4. **Reaction Time Improvement**: Death 신호 적용 시 Reaction Time이 (+)로 전환되는가?

---

## 4. 산출물 (Output Artifacts)

### 4.1 `mining_report.csv`

- 피처별 중요도(Feature Importance), 분포 요약(Percentiles), 최적 임계값(Threshold) 후보.

### 4.2 `Policy_v1_candidates.json`

- 마이닝된 신호를 조합한 신규 진입/청산 룰 제안.
  - 예: `IF Rank_Vel > 5 AND Vol_Accel > 2.0 THEN BUY`

### 4.3 `ablation_matrix.csv` (권장)

- 단일 피처/조합 피처의 성능 비교(Precision/Recall/F1/Regret/Turnover).

---

## 5. Policy v1 (초안 템플릿)

> 아래는 “계약 상 권장되는” 검증 템플릿이며, 실제 Threshold는 `mining_report.csv` 결과로 확정한다.

### 5.1 Birth (Entry) Template

- 조건(예시):
  - Universe: Top-10 내
  - `Vol_Accel >= X`
  - `ROC_5m <= -Y` (눌림목 조건)
  - Optional: `Rank_Velocity >= Z` (상승 랭크 가속)

### 5.2 Death (Exit) Template

- 조건(예시):
  - `VWAP_Div >= A` (과열 익절)
  - OR `ROC_5m <= -B` (급락/모멘텀 붕괴 손절)
  - Optional: `Rank_Stability` 붕괴(Top-K 이탈 지속)

---

## 6. 비기능 요구사항 (Non-Functional Requirements)

- **Lookahead 금지**: 모든 피처는 시각 $t$까지의 데이터만 사용.
- **재현성**: 동일 입력 데이터로 동일 산출물이 재생성 가능해야 함(Seed 고정).
- **Audit 적합성**: Policy v1 검증은 Gate A/B/C 및 Cost Toggle Test로 통과해야 함.

---

## 부록 A. 참조 코드 (Non-normative Reference)

아래 코드는 계약의 “참조 구현 스켈레톤”이며, 프로젝트 구조에 맞게 조정한다.

### A.1 분석 스크립트(분포/통계) - `scripts/mining/analyze_mining_results.py`

```python
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
mining_dir = project_root / "results" / "mining" / "week1"

def analyze_features(filename, target_name):
    path = mining_dir / filename
    if not path.exists():
        print(f"File not found: {filename}")
        return

    df = pd.read_csv(path)
    print(f"\n[{target_name} Analysis] Total Samples: {len(df)}")
    
    # Split by Label
    pos = df[df['label'] == 1]
    neg = df[df['label'] == 0]
    
    features = ['vol_accel', 'vwap_div', 'roc_5m']
    
    print(f"Positive (Event): {len(pos)} | Negative (Control): {len(neg)}")
    
    for feat in features:
        print(f"\n>>> Feature: {feat}")
        p_mean = pos[feat].mean()
        n_mean = neg[feat].mean()
        p_std = pos[feat].std()
        
        print(f"  Pos Mean: {p_mean:.4f} (+/- {p_std:.4f})")
        print(f"  Neg Mean: {n_mean:.4f}")
        print(f"  Delta: {p_mean - n_mean:.4f}")
        
        # Percentiles
        print(f"  Pos [25%, 50%, 75%]: {np.percentile(pos[feat], [25, 50, 75])}")
        print(f"  Neg [25%, 50%, 75%]: {np.percentile(neg[feat], [25, 50, 75])}")

def run_analysis():
    analyze_features("mining_birth_features.csv", "Birth (Entry)")
    analyze_features("mining_death_features.csv", "Death (Exit)")

if __name__ == "__main__":
    run_analysis()
```

### A.2 샘플 생성기(라벨 기반 피처 추출) - `scripts/mining/run_birth_death_mining.py`

```python
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class SignalMiner:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.hero_segments = self.load_all_hero_segments()
        self.out_dir = project_root / "results" / "mining" / "week1"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.birth_samples = []
        self.death_samples = []
        
    def load_all_hero_segments(self):
        segments = []
        current = self.start_date
        while current <= self.end_date:
            ymd = current.strftime("%Y%m%d")
            path = project_root / "results" / "labels" / f"day={ymd}" / "hero_segments.csv"
            if path.exists():
                df = pd.read_csv(path)
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
                segments.append(df)
            current += timedelta(days=1)
        return pd.concat(segments, ignore_index=True) if segments else pd.DataFrame()

    def load_minute_data(self, symbol, date_str):
        p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(symbol).zfill(6)}.csv"
        if not p.exists():
            return None
        df = pd.read_csv(p, usecols=['date', 'open', 'high', 'low', 'close', 'volume'])
        df = df[df['date'].astype(str).str.startswith(date_str)].copy()
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        df.set_index('date', inplace=True)
        return df

    def extract_features(self, df, t_target, lookback=10):
        start_win = t_target - timedelta(minutes=lookback)
        ts_slice = df.loc[start_win:t_target]
        if len(ts_slice) < 5:
            return None
        
        current_close = ts_slice['close'].iloc[-1]
        current_vol = ts_slice['volume'].iloc[-1]
        
        vol_ma = ts_slice['volume'].mean()
        vol_accel = current_vol / vol_ma if vol_ma > 0 else 0
        
        cum_vol = ts_slice['volume'].cumsum()
        cum_pv = (ts_slice['close'] * ts_slice['volume']).cumsum()
        vwap_local = cum_pv.iloc[-1] / cum_vol.iloc[-1] if cum_vol.iloc[-1] > 0 else current_close
        vwap_div = (current_close / vwap_local) - 1.0
        
        p_5m_ago = ts_slice['close'].iloc[-5] if len(ts_slice) >= 5 else ts_slice['close'].iloc[0]
        roc_5 = (current_close / p_5m_ago) - 1.0
        
        return {"vol_accel": vol_accel, "vwap_div": vwap_div, "roc_5m": roc_5}

    def run(self):
        total_segs = len(self.hero_segments)
        for idx, seg in self.hero_segments.iterrows():
            if idx % 50 == 0: print(f"Processing {idx}/{total_segs}...")
            sym = seg['symbol']
            t_start = seg['start_time']
            t_end = seg['end_time']
            date_str = t_start.strftime("%Y%m%d")
            df = self.load_minute_data(sym, date_str)
            if df is None or df.empty:
                continue
            
            # Birth positive
            t_birth = t_start - timedelta(minutes=1)
            feats = self.extract_features(df, t_birth)
            if feats:
                feats.update({"label": 1, "symbol": sym, "time": t_birth})
                self.birth_samples.append(feats)
            
            # Birth negative (far before)
            t_neg = t_start - timedelta(minutes=30)
            if t_neg in df.index:
                feats = self.extract_features(df, t_neg)
                if feats:
                    feats.update({"label": 0, "symbol": sym, "time": t_neg})
                    self.birth_samples.append(feats)

            # Death positive
            t_death = t_end - timedelta(minutes=1)
            feats = self.extract_features(df, t_death)
            if feats:
                feats.update({"label": 1, "symbol": sym, "time": t_death})
                self.death_samples.append(feats)

            # Death negative (mid segment)
            t_mid = (t_start + (t_end - t_start) / 2).round('1T')
            if t_mid in df.index:
                feats = self.extract_features(df, t_mid)
                if feats:
                    feats.update({"label": 0, "symbol": sym, "time": t_mid})
                    self.death_samples.append(feats)

        self.save_results()

    def save_results(self):
        pd.DataFrame(self.birth_samples).to_csv(self.out_dir / "mining_birth_features.csv", index=False)
        pd.DataFrame(self.death_samples).to_csv(self.out_dir / "mining_death_features.csv", index=False)
        print(f"Saved {len(self.birth_samples)} birth samples and {len(self.death_samples)} death samples.")

if __name__ == "__main__":
    SignalMiner("2025-12-15", "2025-12-19").run()
```
