# -*- coding: utf-8 -*-
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
import glob
from concurrent.futures import ThreadPoolExecutor
import random
import datetime

# --- DNA Loading ---
def load_tactical_dna(dna_path: Path):
    if not dna_path.exists():
        print(f"[WARN] DNA file {dna_path} not found. using defaults.")
        return {}
    try:
        data = json.loads(dna_path.read_text(encoding='utf-8'))
        print(f"[DNA] Loaded {len(data.get('params', {}))} params from {dna_path.name}")
        return data.get("params", {})
    except Exception as e:
        print(f"[ERR] Failed to load DNA: {e}")
        return {}

# --- Configuration & Constants ---
DNA_PATH = Path("c:/garam/garam/core/active_config/tactical_dna.json")
DNA_PARAMS = load_tactical_dna(DNA_PATH)

FEE_BPS = 5.0 
SLIPPAGE_BPS = 5.0 
CAPITAL = DNA_PARAMS.get("solo_capital_limit", 10_000_000)

# "Genius" Params from DNA
TRAILING_STOP_PCT = DNA_PARAMS.get("trailing_stop_pct", 0.010) # DNA says 0.07 (7%)?
STOP_LOSS_PCT = DNA_PARAMS.get("solo_trailing_stop", 0.012)    # DNA uses this field maybe?
if STOP_LOSS_PCT > 0.1: STOP_LOSS_PCT = 0.012 # Safety fallback if parsing fails

class AlphaBase:
    def __init__(self):
        self.name = "Base"
    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

class AlphaGenius_V2(AlphaBase):
    """
    AlphaGenius V2: 진화하는 신경망 (Evolving Nervous System)
    1. 진입 (Entry): 응축(Coiling) + 15분봉 프랙탈 정렬
    2. 비중 (Sizing): '신경 점수(Neuro Score)' (0-10) 기반 가변 베팅
    3. 청산 (Exit): 에너지 소진(Exhaustion) 감지 시 '스텔스 엑시트'
    """
    def __init__(self, mode="STANDARD", risk_guard="NONE"):
        super().__init__()
        self.name = "AlphaGenius_V2"
        self.mode = mode
        self.risk_guard = risk_guard
        
        # [EVOLUTION] Initial Genes (Parameters)
        self.params = {
            'rsi_low': 30.0,
            'vol_explosive': 3.0,
            'vol_quiet': 1.0,
            'vol_panic': 2.0,
            'breakout_th': 0.005
        }
        self.last_reasons = None
        self.last_state_map = None # [NEURO] Detailed State for Brain
        print(f"[Neuro] Activated Mode: {self.mode} | Risk Guard: {self.risk_guard} | Genes: {len(self.params)}")

    def evolve(self, feedback: dict):
        """
        [Meta-Learning] Adjust parameters based on feedback.
        feedback = {'S3_success': True/False, 'volatility': 'high'}
        """
        # Simple mutation logic for demonstration
        # If 'S3 (Hunter)' failed, maybe RSI threshold was too high (not oversold enough)
        if feedback.get('strategy') == 'S3' and not feedback.get('success'):
            self.params['rsi_low'] = max(10.0, self.params['rsi_low'] - 1.0)
            print(f"[EVOLVE] 📉 Tightening Hunter RSI Threshold -> {self.params['rsi_low']:.1f}")
            
        # If 'S2 (Charger)' succeeded, maybe we can be bolder? or just keep it.
        # If 'S1 (Sniper)' failed, maybe volume requirement for 'quiet' is too strict?
        if feedback.get('strategy') == 'S1' and not feedback.get('success'):
             self.params['vol_quiet'] = min(2.0, self.params['vol_quiet'] + 0.1)
             print(f"[EVOLVE] 🔬 Relaxing Sniper Quiet Threshold -> {self.params['vol_quiet']:.2f}")

    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        print("[Neuro System] AlphaGenius V2 신경망 활성화 중...")
        
        # [EVOLUTION] Use Self-Optimizing Parameters
        # These evolve over time based on feedback
        p_rsi_low = self.params.get('rsi_low', 30.0)
        p_vol_explosive = self.params.get('vol_explosive', 3.0)
        p_vol_panic = self.params.get('vol_panic', 2.0)
        p_vol_quiet = self.params.get('vol_quiet', 1.0)
        p_breakout_th = self.params.get('breakout_th', 0.005)
        
        # --- 0. 시장 기류 분석 (Market Regime Analysis) ---
        # 전체 시장의 평균 변동성 측정
        # 각 종목의 20일 변동성 평균
        returns = closes.pct_change()
        vol_20 = returns.rolling(window=20).std()
        market_vol = vol_20.mean(axis=1) # Market Average Volatility
        
        # 장기 평균 대비 현재 변동성 비율
        # (변동성이 크면 -> 기준을 높여서 보수적으로)
        # (변동성이 작으면 -> 기준을 낮춰서 공격적으로...가 아니라, 보통 변동성 크면 기회도 많지만 위험도 큼)
        # 사용자 공식: Threshold = Base * (Vol_Market / Vol_Avg) + Risk
        
        vol_avg_100 = market_vol.rolling(window=100).mean()
        vol_ratio = (market_vol / (vol_avg_100 + 1e-9)).fillna(1.0)
        
        # Risk Sentiment (간단히 하락장에서 Risk 높음)
        # MA20 아래 있는 종목 비율로 공포 지수 산출
        ma20 = closes.rolling(window=20).mean()
        below_ma20 = (closes < ma20).sum(axis=1) / closes.shape[1]
        risk_sentiment = below_ma20 # 0.0 ~ 1.0 (1.0 = All crash)
        
        # Dynamic Threshold Calculation
        base_score_threshold = 5.0
        # 변동성이 2배면 문턱 10점? 너무 높음. Scaled.
        # Ratio 1.0 -> 5.0
        # Ratio 2.0 -> 7.0 (Slightly higher)
        # Risk 0.8 -> +2.0
        
        # Formula Implementation
        # Threshold = 4.0 * (0.8 + 0.2 * Vol_Ratio) + (Risk * 1.5)
        # Example: Normal Vol (1.0), Low Risk (0.2) -> 4.0 * 1.0 + 0.3 = 4.3 (Open to ideas)
        dynamic_thresh = 4.0 * (0.8 + 0.2 * vol_ratio) + (risk_sentiment * 1.5)
        
        # Reindex to 1m
        thresh_1m = dynamic_thresh.reindex(closes.index, method='ffill').fillna(5.0)
        
        print(f"[Regime] Market Vol Ratio: {vol_ratio.iloc[-1]:.2f}, Risk: {risk_sentiment.iloc[-1]:.2f}")
        print(f"[Regime] Dynamic Threshold: {thresh_1m.iloc[-1]:.2f} (Base: 5.0)")

        # --- 1. 시냅스 입력 (타임프레임 동기화) ---
        # 15분봉 프랙탈 추세 (Parent Wave)
        c_15m = closes.resample('15min', label='right').last()
        ma20_15m = c_15m.rolling(window=20).mean()
        # 15분봉 추세를 1분봉에 매핑
        trend_15m = (c_15m > (ma20_15m + 1e-9)).reindex(closes.index, method='ffill').fillna(False)
        
        # [OPTIMIZATION] Use Vectorized Numpy for Speed
        c_vals = closes.values
        v_vals = volumes.values
        
        # 5분봉 응축 (The Trigger) - Approximate 5m using 5-step rolling on 1m
        # This is faster than resampling entire dataframe
        c_5m_equiv = closes.iloc[::5] # Slice every 5th
        v_5m_equiv = volumes.rolling(5).sum().iloc[::5]
        
        # 볼린저 밴드 (Numpy based)
        # rolling_5m = c_5m.rolling(window=20) -> c_5m_equiv.rolling(20)
        ma20 = c_5m_equiv.rolling(window=20).mean()
        std20 = c_5m_equiv.rolling(window=20).std()
        
        upper = ma20 + 2*std20
        lower = ma20 - 2*std20
        bb_width = (upper - lower) / (ma20 + 1e-9)
        
        # 밴드 폭의 상대적 위치 (Z-Score)
        width_mean = bb_width.rolling(window=100).mean()
        width_std = bb_width.rolling(window=100).std()
        width_z = (bb_width - width_mean) / (width_std + 1e-9)
        
        width_mean = bb_width.rolling(window=100).mean()
        width_std = bb_width.rolling(window=100).std()
        width_z = (bb_width - width_mean) / (width_std + 1e-9)
        
        # [DIAGNOSTIC] Extremely relaxed conditions to generate signals
        is_squeezed = (width_z < 1.5)  # Much more permissive
        
        # 거래량 폭발 (The Fuel)
        v_ma20_5m = v_5m_equiv.rolling(window=20).mean()
        vol_ratio = (v_5m_equiv / (v_ma20_5m + 1e-9)).fillna(0.0)
        is_vol_exploded = (vol_ratio > 1.0)  # Any above-average volume
        
        # [FEATURE] Whale Accumulation Scan (Long-term Vision: 120 periods = 10 hours of 5m bars?) 
        # Actually 120 of 1m bars = 2 hours. Let's look at 480 (1 day) for structure.
        c_long = closes.rolling(window=480).mean() # 1-day trend
        is_uptrend_long = (closes > c_long)
        
        # Whale Footprint: High Volume but Price Stable (Accumulation)
        # Low volatility over 60 mins AND High Volume Ratio
        volatility_60 = closes.pct_change().rolling(60).std()
        volume_60 = volumes.rolling(60).sum()
        avg_vol_60 = volumes.rolling(480).sum() / 8.0 # Approx 
        
        is_quiet_accumulation = (volatility_60 < volatility_60.rolling(480).mean()) & (volume_60 > avg_vol_60 * 1.5)
        
        # --- PROPHET LOGIC (V3 Integration) ---
        # 1. Churning Detection (High Vol, Low Move) = Distribution/Trap
        # VolRatio > 3.0 AND Abs(Ret) < 0.2%
        # c_5m -> c_5m_equiv
        ret_5m = c_5m_equiv.pct_change().fillna(0)
        is_churning = (vol_ratio > 3.0) & (ret_5m.abs() < 0.002)
        churn_1m = is_churning.reindex(closes.index, method='ffill').fillna(False)
        
        # 2. Hurdle Rate (Dynamic Minimum Reward)
        # Survivorship Bias: Don't take trades unless potential > friction.
        # Potential = 5 * ATR
        tr = closes.diff().abs()
        atr = tr.rolling(14).mean()
        potential_reward = (5.0 * atr) / closes
        
        # Dynamic Hurdle:
        # If Risk High (Panic): Need > 3.5% reward.
        # If Risk Low (Normal): Need > 1.5% reward.
        hurdle = 0.015 + (risk_sentiment * 0.02) # 1.5% ~ 3.5%
        
        is_worth_it = potential_reward.gt(hurdle, axis=0) # Pass if Potential > Hurdle
        
        # 구조적 지지 (The Floor) - 일봉 MA60
        c_daily = closes.resample('D').last().ffill()
        ma60_daily = c_daily.rolling(window=60).mean().shift(1).reindex(closes.index, method='ffill')
        # [Fix] SyntaxError 해결: 할당 표현식 분리
        is_above_structure = closes.gt(ma60_daily, axis=0)
        
        # Apply Prophet Filters to Final Mask
        # Must NOT be churning AND Must be worth it
        
        # Reindex 5m signals to 1m
        sq_1m = is_squeezed.reindex(closes.index, method='ffill').fillna(False)
        ve_1m = is_vol_exploded.reindex(closes.index, method='ffill').fillna(False)
        
        # Prophet Filter Debug
        print(f"[Prophet] Churn Filtered Bars: {churn_1m.sum().sum()}")
        print(f"[Prophet] Hurdle Filtered Bars: {(~is_worth_it).sum().sum()}")

        # ============================================
        # [CRITICAL FIX] Calculate RSI BEFORE mode branching
        # This ensures RSI is available in all code paths
        # ============================================
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))

        # ============================================
        # [ULTRA AGGRESSIVE MODE] - 수익 극대화 모드
        # ============================================
        if self.mode == "ULTRA_AGGRESSIVE":
            # 1. Base Trigger: Any positive momentum with volume
            ret_1m = closes.pct_change(5).fillna(0)
            positive_momentum = (ret_1m > 0)
            has_volume = (volumes > 0)

            # 2. Relaxed Technicals (OR conditions for maximum sensitivity)
            # Strategy A: Squeeze (Sniper)
                # Strategy D: Whale Rider (Accumulation Breakout)
            # Find zones where volume was high but price was flat (Whale footprints)
            whale_footprint = is_quiet_accumulation 
            whale_breakout = whale_footprint & (closes > closes.shift(1).rolling(20).max())
            
            # Strategy E: Short-Squeeze Predator
            # High volume (Panic Cover) + Price surge (Shortest time, max move)
            is_squeeze = (closes > closes.shift(1).rolling(5).max()) & (vol_ratio > 8.0)
            
            # [LEARNING] Load strategy weights (if available)
            strategy_weights = {'S1': 1.0, 'S2': 1.0, 'S3': 1.0, 'S4': 1.0, 'S5': 1.0}
            
            # Combine for Final Confidence Score with ADAPTIVE WEIGHTS
            # Sniper(S1), Charger(S2), Hunter(S3), Whale(S4), Squeeze(S5)
            s1 = (sq_1m & ve_1m).astype(float) * 4.0 * strategy_weights['S1']
            s2 = (ve_1m & (ret_1m > 0)).astype(float) * 3.0 * strategy_weights['S2']
            s3 = (rsi < p_rsi_low).astype(float) * 5.0 * strategy_weights['S3']
            s4 = whale_breakout.astype(float).reindex(closes.index, method='ffill').fillna(0) * 6.0 * strategy_weights['S4']
            s5 = is_squeeze.astype(float).reindex(closes.index, method='ffill').fillna(0) * 8.0 * strategy_weights['S5']
            
            neuro_score = s1 + s2 + s3 + s4 + s5
            
            # Prophet Sanity Check
            neuro_score = neuro_score.where(~churn_1m, neuro_score * 0.5) # Half score on churn/trap
            neuro_score = neuro_score.where(is_worth_it, 0.0)             # Zero score if not worth the friction
            
            # Save Reasons for logging
            reasons = pd.DataFrame("", index=closes.index, columns=closes.columns)
            reasons.where(~whale_breakout.reindex(closes.index, method='ffill').fillna(False), "S4(Whale)", inplace=True)
            reasons.where(~is_squeeze.reindex(closes.index, method='ffill').fillna(False), "S5(SQUEEZE)", inplace=True)
            self.last_reasons = reasons
            
            # MA distance for Brain
            ma20_1m = closes.rolling(window=20).mean()
            ma_dist = (closes / (ma20_1m + 1e-9)) - 1.0

            # State Map for Brain (INCLUDING STRATEGY WEIGHTS FOR RUNTIME ACCESS)
            self.last_state_map = {
                'rsi': rsi,
                'vol_ratio': vol_ratio.reindex(closes.index, method='ffill').fillna(1.0),
                'width_z': width_z.reindex(closes.index, method='ffill').fillna(0.0),
                'trend_15m': trend_15m.astype(float),
                'whale': whale_footprint.astype(float).reindex(closes.index, method='ffill').fillna(0.0),
                'squeeze': is_squeeze.astype(float).reindex(closes.index, method='ffill').fillna(0.0),
                'ma_dist': ma_dist.fillna(0.0),
                'strategy_weights': strategy_weights  # CRITICAL: Store weights for updates
            }
            
            return neuro_score.fillna(0.0)

        # --- Base Scenarios ---
            
            # S2 [Charger]: Explosive + Breakout + Whale Backing -> The Ride
            s2_charger = state_explosive & is_breakout & is_uptrend_long
            
            # S3 [Hunter]: Explosive + Oversold -> The Reversal
            s3_hunter = state_explosive & is_oversold
            
            # S4 [Flow]: Just strong momentum with structure
            s4_flow = positive_momentum & is_above_structure & has_volume
            
            # Combined Trigger: Any valid scenario
            tech_trigger = s1_sniper | s2_charger | s3_hunter | s4_flow
            
            # Structure Filter:
            # Hunter doesn't need structure. Others do.
            # Logic: If Hunter, pass. If others, need structure.
            # Simplified: tech_trigger handles the logic per scenario.
            
            core_signal = tech_trigger & has_volume
            
            # 3. RISK GUARD: MA60_STRUCTURAL (The Playground)
            if self.risk_guard == "MA60_STRUCTURAL":
                core_signal = core_signal & is_above_structure
                print("[Risk] MA60 Structural Filter Applied.")
            
            final_mask = core_signal
        else:
             # Standard Mode (Original)
             core_signal = is_squeezed & is_vol_exploded
             final_mask = core_signal & trend_15m


        # [NEURO] Prepare State Map (For 64-dim Neural Input)
        # RSI is already calculated before mode branching

        self.last_state_map = {
            'vol_ratio': vol_ratio.reindex(closes.index, method='ffill').fillna(0),
            'width_z': width_z.reindex(closes.index, method='ffill').fillna(0),
            'rsi': rsi.reindex(closes.index, method='ffill').fillna(50),
            'trend_15m': trend_15m.astype(float),
            'ma_dist': (closes / ma20.reindex(closes.index, method='ffill') - 1.0).fillna(0),
            # [Fix] Added missing keys for Brain compatibility
            'whale': is_quiet_accumulation.astype(float).reindex(closes.index, method='ffill').fillna(0),
            'squeeze': is_squeezed.astype(float).reindex(closes.index, method='ffill').fillna(0)
        }

        print(f"[{self.mode}] Total Signal Bars: {final_mask.sum().sum()}")
        
        # --- 2. 신경 처리 (Neuro Processing) ---
        # A. 상대적 히어로 포착 (Relative Hero)
        # 평소 거래량이 100주인데 500주 터진 놈 (Relative to Self) -> 이미 vol_ratio로 반영됨
        # 평소 시장 평균 대비 압도적인 놈 (Relative to Market) -> 추가
        
        # 시장 전체 평균 거래량 (5분봉) - 0으로 나누기 방지
        market_mean_vol = v_5m_equiv.mean(axis=1).replace(0, 1e-9)
        # 나의 거래량 vs 시장 평균 거래량
        relative_strength = v_5m_equiv.div(market_mean_vol, axis=0).fillna(0)
        # 시장 평균보다 5배 더 활발한 종목 (주도주)
        is_relative_hero = (relative_strength > 5.0).reindex(closes.index, method='ffill').fillna(False)
        
        # B. 점수 산출 (Scoring)
        # Base Score (기본 점수): 5.0
        base_points = final_mask.astype(float) * 5.0
        
        # 1분봉으로 리샘플링된 지표 정의 (Missing Fix)
        z_1m = width_z.reindex(closes.index, method='ffill').fillna(0)
        vr_1m = vol_ratio.reindex(closes.index, method='ffill').fillna(0)

        # Quality Boosts
        tight_squeeze_boost = ((z_1m < -0.5) & final_mask).astype(float) * 2.0
        huge_vol_boost = ((vr_1m > 3.0) & final_mask).astype(float) * 2.0
        fractal_boost = (trend_15m & final_mask).astype(float) * 1.0 
        rel_hero_boost = (is_relative_hero & final_mask).astype(float) * 1.0 
        # Structure Boost (Previously a filter)
        structure_safety_boost = (is_above_structure & final_mask).astype(float) * 2.0
        
        rel_hero_boost = (is_relative_hero & final_mask).astype(float) * 1.0 
        # Structure Boost (Previously a filter)
        structure_safety_boost = (is_above_structure & final_mask).astype(float) * 2.0
        
        # Scenario Bonus (Reward specific high-quality setups)
        # [Fix] Define Fallback Signals for Standard Mode Scoring
        if 's1_sniper' not in locals():
            s1_sniper = (width_z < 0.5) & (vol_ratio > 2.0) # Squeeze + Pop
        if 's3_hunter' not in locals():
            s3_hunter = (vol_ratio > 3.0) & (rsi < 30)      # Oversold Reversal
            
        # Reindex scenarios to 1m
        s1_boost = (s1_sniper.reindex(closes.index, method='ffill').fillna(False) & final_mask).astype(float) * 3.0
        s3_boost = (s3_hunter.reindex(closes.index, method='ffill').fillna(False) & final_mask).astype(float) * 2.0
        
        raw_neuro_score = base_points +\
                          tight_squeeze_boost + huge_vol_boost + fractal_boost + rel_hero_boost + structure_safety_boost +\
                          s1_boost + s3_boost
        
        # C. 동적 임계치 적용 (Dynamic Thresholding)
        # 시장 상황(Regime)에 따라 요구되는 점수가 다름
        # 공포장(High Vol) -> 임계치 8.0 이상 필요
        # 평온장(Low Vol) -> 임계치 5.0 이상이면 OK
        
        # Align Threshold to 1m columns
        # thresh_1m is Series (T,), raw_neuro_score is DF (T, N)
        # Broadcast comparison
        meets_threshold = raw_neuro_score.ge(thresh_1m, axis=0)
        
        # Final Score: Only keep scores that meet the dynamic threshold
        neuro_score = raw_neuro_score * meets_threshold.astype(float)
        
        if self.mode == "ULTRA_AGGRESSIVE":
            # Assign codes to reasons
            reason_df = pd.DataFrame("", index=closes.index, columns=closes.columns)
            # Higher priority overrides lower? Or concatenate?
            # Let's simple overwrite priority S3 > S1 > S2
            reason_df[s4_flow] = "S4"
            reason_df[s2_charger] = "S2"
            reason_df[s1_sniper] = "S1"
            reason_df[s3_hunter] = "S3" # Hunter overrides
            
            self.last_reasons = reason_df.shift(1).fillna("")
        
        print(f"[Neuro] 생성된 신호 수 (Raw): {(raw_neuro_score > 0).sum().sum()}")
        print(f"[Neuro] 임계치 통과 신호 수 (Filtered): {(neuro_score > 0).sum().sum()}")
        print(f"[Neuro] 최고 확신 점수: {neuro_score.max().max()}")
        
        # [DEBUG] Check Shapes
        for k, v in self.last_state_map.items():
            if hasattr(v, 'shape'):
                print(f"[DEBUG] State '{k}' shape: {v.shape}")
            else:
                print(f"[DEBUG] State '{k}' type: {type(v)}")
        
        return neuro_score.shift(1).fillna(0.0)

    def calculate_exhaustion(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        """
        '스텔스 엑시트(Stealth Exit)' 조건 감지:
        1. 거래량 클라이맥스(Volume Climax): 거래량이 평소의 4배 이상 폭발 (패닉 바잉)
        2. 수급 역전(Flow Reversal): 거래량은 터지는데 가격 상승이 멈춤 (RSI 과열 + 물량 넘기기)
        """
        # RSI 14구간 계산
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        
        # 거래량 클라이맥스 정의
        v_ma20 = volumes.rolling(window=20).mean()
        vol_climax = (volumes > 6.0 * v_ma20) & (v_ma20 > 0)
        
        # 과열 상태 정의
        is_overheated = (rsi > 75)
        
        # 스텔스 엑시트 신호: 과열권에서 거래량만 터지고 가격이 못 갈 때
        # "에너지가 고갈되었다는 직관적 신호"
        stealth_exit = is_overheated & vol_climax
        
        return stealth_exit.fillna(False)

def parse_minute_csv(filepath):
    try:
        df = pd.read_csv(filepath)
        cols = [c.lower() for c in df.columns]
        df.columns = cols
        if "datetime" in df.columns: df = df.rename(columns={"datetime": "date"})
        if "volume" not in df.columns: df["volume"] = 0.0
        
        # Helper for formats
        if "date" in df.columns:
             # Try YYYYMMDDHHMMSS first
             df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
             # Try YYYYMMDDHHMM
             if df["dt"].isnull().all():
                 df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
        
        df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
        return df[["close", "volume"]]
    except:
        return pd.DataFrame()

def load_data(data_dir, universe_file, start_date, end_date):
    print(f"[Loader] Loading data {start_date} to {end_date}...")
    # Minimal universe loading
    try:
        u_df = pd.read_csv(universe_file)
        symbols = [str(x).zfill(6) for x in u_df.iloc[:,0].tolist()] # Assume col 0 is symbol
    except:
        # scan dir
        files = glob.glob(str(data_dir / "*.csv"))
        symbols = [Path(f).stem for f in files][:50] # Limit to 50 for speed in test
    
    closes, volumes = {}, {}
    s_dt, e_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
    
    def _load(sym):
        f = data_dir / f"{sym}.csv"
        if not f.exists(): return None, None, None
        df = parse_minute_csv(f)
        if df.empty: return None, None, None
        mask = (df.index >= s_dt) & (df.index <= e_dt)
        df = df.loc[mask]
        if df.empty: return None, None, None
        return sym, df["close"], df["volume"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        for sym, c, v in executor.map(_load, symbols):
           if sym:
               closes[sym] = c
               volumes[sym] = v
               
    print(f"[Loader] Loaded {len(closes)} symbols.")
    return pd.DataFrame(closes), pd.DataFrame(volumes)

def apply_noise(df: pd.DataFrame, intensity: float = 0.001) -> pd.DataFrame:
    """Inject Gaussian noise to prices"""
    print(f"[Noise] Injecting {intensity*100}% noise...")
    noise = np.random.normal(0, intensity, df.shape)
    return df * (1 + noise)

def simulate_crash(df: pd.DataFrame, prob: float = 0.01, drop: float = 0.05) -> pd.DataFrame:
    """Randomly drop prices by 'drop' pct with 'prob' probability per day"""
    # Simply apply to random rows? No, a crash is a market-wide event.
    # Group by Day
    print(f"[Gauntlet] Simulating Crashes (Prob={prob*100}%, Drop={drop*100}%)...")
    daily_groups = df.groupby(df.index.date)
    new_days = []
    
    for day, day_df in daily_groups:
        if random.random() < prob:
            # CRASH DAY: Drop price significantly
            # Linear decay during the day or instant gap? 
            # Gap down at open: everything -5%
            day_df = day_df * (1.0 - drop)
            print(f" -> CRAASH on {day}!")
        new_days.append(day_df)
    
    return pd.concat(new_days).sort_index()

def shuffle_days(closes, volumes):
    """
    Shuffles date order to break memory.
    Returns: List of (DayDate, ClosesDF, VolumesDF) tuples in Random Order
    """
    print("[Shuffling] Randomizing Day Order...")
    dates = sorted(list(set(closes.index.date)))
    random.shuffle(dates)
    
    shuffled_data = []
    for d in dates:
        # Slice for this day
        # Need string format for slicing usually, or boolean mask
        mask = (closes.index.date == d)
        c_day = closes.loc[mask]
        v_day = volumes.loc[mask]
        shuffled_data.append((d, c_day, v_day))
        
    return shuffled_data

def run_strategy_shuffled(alpha: AlphaBase, closes: pd.DataFrame, volumes: pd.DataFrame, out_dir: Path, 
                          do_noise=False, do_shuffle=False, do_crash=False):
    
    # 1. 신호 및 스텔스 엑시트 사전 계산
    print("[Engine] 타임라인 정렬 및 신호/청산 로직 계산 중...")
    signals_chronological = alpha.calculate_signals(closes, volumes)
    
    # 스텔스 엑시트 신호 계산 (신경망 V2인 경우)
    if hasattr(alpha, 'calculate_exhaustion'):
        exhaustion_signals = alpha.calculate_exhaustion(closes, volumes)
    else:
        exhaustion_signals = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    
    # 2. 데이터 변형 (노이즈/크래시) 적용
    if do_crash:
        closes = simulate_crash(closes, prob=0.05, drop=0.08)
    
    if do_noise:
        closes = apply_noise(closes, intensity=0.002)
        
    # 데이터 변형 후 신호 재계산 (변형된 가격에 반응하는지 테스트)
    signals = alpha.calculate_signals(closes, volumes)
    # 스텔스 엑시트도 재계산
    if hasattr(alpha, 'calculate_exhaustion'):
        exhaustion_signals = alpha.calculate_exhaustion(closes, volumes)
    
    # 3. 셔플링 시퀀스 생성
    day_blocks = []
    all_dates = sorted(list(set(closes.index.date)))
    
    for d in all_dates:
        mask = (closes.index.date == d)
        c_day = closes.loc[mask]
        v_day = volumes.loc[mask]
        s_day = signals.loc[mask]
        e_day = exhaustion_signals.loc[mask] # Exhaustion Block
        day_blocks.append({"date": d, "c": c_day, "v": v_day, "s": s_day, "e": e_day})
        
    if do_shuffle:
        random.shuffle(day_blocks)
        print("[Shuffling] 과거의 기억을 지우는 중 (Day Shuffling)...")
        
    # 4. 시뮬레이션 루프
    cash = CAPITAL
    equity_curve = []
    trade_rows = []
    
    total_trades = 0
    
    for block in day_blocks:
        d_date = block["date"]
        c_blk = block["c"]
        s_blk = block["s"]
        e_blk = block["e"]
        
        pos_sym = None
        pos_qty = 0.0
        entry_px = 0.0
        
        daily_start_cash = cash
        
        for ts, row in c_blk.iterrows():
            prices = row
            sigs = s_blk.loc[ts]
            exh = e_blk.loc[ts]
            
            current_val = cash
            if pos_sym:
                 px = prices[pos_sym]
                 current_val += pos_qty * px
                 
                 # 1. 스텔스 엑시트 (에너지 고갈 감지)
                 # 보유 종목에 대해 'exhaustion' 신호가 뜨면 즉시 탈출
                 if pos_sym in exh.index and exh[pos_sym]:
                     # 스텔스 청산
                     cash += pos_qty * px * (1 - FEE_BPS/10000)
                     trade_rows.append({"ts": ts, "sym": pos_sym, "pnl_pct": (px/entry_px)-1, "reason": "STEALTH_EXIT(에너지고갈)"})
                     pos_sym = None
                     continue # 다음 루프로

                 # 2. 기존 트레일링 스탑/익절
                 ret = (px / entry_px) - 1.0
                 if ret < -TRAILING_STOP_PCT: 
                     cash += pos_qty * px * (1 - FEE_BPS/10000)
                     trade_rows.append({"ts": ts, "sym": pos_sym, "pnl_pct": ret, "reason": "STOP(손절)"})
                     pos_sym = None
                 elif ret > 0.15: 
                     cash += pos_qty * px * (1 - FEE_BPS/10000)
                     trade_rows.append({"ts": ts, "sym": pos_sym, "pnl_pct": ret, "reason": "PROFIT(익절)"})
                     pos_sym = None
            
            equity_curve.append({"ts": ts, "equity": current_val})
            
            # 진입 로직 (Entry)
            if not pos_sym:
                # 점수가 0보다 큰 종목 찾기
                candidates = sigs[sigs > 0].sort_values(ascending=False)
                if not candidates.empty:
                    best_sym = candidates.index[0]
                    score = candidates.iloc[0] # Neuro Score
                    
                    # Kelly Criterion 적용 (자금 배분의 지능화)
                    # Score 9.0 이상: '승부수' (1.0 배팅)
                    # Score 5.0 이상: '정찰대' (0.5 배팅)
                    alloc_ratio = 0.5 # Default
                    entry_type = "정찰대(Std)"
                    
                    if score >= 9.0:
                        alloc_ratio = 1.0
                        entry_type = "승부수(Big)"
                    elif score >= 7.0:
                         alloc_ratio = 0.7
                         entry_type = "주력(Main)"
                         
                    px = prices[best_sym]
                    if px > 0:
                        invest = cash * alloc_ratio 
                        qty = invest / (px * (1 + SLIPPAGE_BPS/10000))
                        cash -= invest
                        pos_sym = best_sym
                        pos_qty = qty
                        entry_px = px
                        trade_rows.append({"ts": ts, "sym": best_sym, "pnl_pct": 0, "reason": f"ENTRY_{entry_type}_Score{score:.1f}"})
        
        # EOD 강제 청산
        if pos_sym:
            last_px = c_blk.iloc[-1][pos_sym]
            cash += pos_qty * last_px * (1 - FEE_BPS/10000)
            trade_rows.append({"ts": str(d_date)+"_EOD", "sym": pos_sym, "pnl_pct": 0, "reason": "EOD_CLOSE(장마감)"})
            pos_sym = None

    # Report
    df_eq = pd.DataFrame(equity_curve)
    df_tr = pd.DataFrame(trade_rows)
    
    if not df_eq.empty:
        final_eq = df_eq.iloc[-1]["equity"]
        ret = (final_eq / CAPITAL) - 1.0
        print(f"[Result] Final Equity: {final_eq:,.0f} ({ret*100:.2f}%)")
        df_eq.to_csv(out_dir / "equity.csv", index=False)
    
    if not df_tr.empty:
        print(f"[Result] Total Trades: {len(df_tr)}")
        df_tr.to_csv(out_dir / "trades.csv", index=False)
        wins = df_tr[df_tr["pnl_pct"] > 0]
        acc = len(wins) / len(df_tr) if len(df_tr) > 0 else 0
        print(f"[Result] Win Rate: {acc*100:.1f}%")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="c:/garam/garam/GARAM_Data/minute/kr")
    parser.add_argument("--universe_file", default="c:/garam/garam/GARAM_Data/raw/universe_test.csv")
    parser.add_argument("--out_dir", default="c:/garam/garam/results/gauntlet_test")
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--noise", action="store_true")
    parser.add_argument("--crash", action="store_true")
    args = parser.parse_args()
    
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    start = "20250601"
    end = "20251212"
    closes, volumes = load_data(Path(args.data_dir), args.universe_file, start, end)
    
    if closes.empty:
        print("No Data.")
        return

    # 2. Run Robust Alpha
    alpha = AlphaGenius_V2()
    run_strategy_shuffled(
        alpha, closes, volumes, out, 
        do_noise=True,    # Always noise for 'Gauntlet'
        do_shuffle=True,  # Always shuffle for 'Gauntlet'
        do_crash=True     # Always crash for 'Gauntlet'
    )

if __name__ == "__main__":
    main()
