# garam_core/analysis/capital_policy.py
"""
Phase 21-C: Capital Policy (자본 배분 정책)

3-Sleeve 구조:
- Reserve: 현금/인출 버퍼 (기본 5%, 인출 시 최대 30%)
- Alpha: 히어로 주식 (히어로 있을 때만)
- Carry: 안전자산 (히어로 없을 때도 95% 유지)

Overnight 예산:
- STRICT: AUM의 최대 60%
- SOFT: AUM의 최대 15%
- NONE: 0%
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Literal
import warnings

from .hero_finder import HeroMetadata


@dataclass
class CapitalPolicyConfig:
    """자본 배분 정책 설정"""
    # Reserve Sleeve
    reserve_base: float = 0.05           # 기본 Reserve 5%
    reserve_max: float = 0.30            # Reserve 상한 30%
    reserve_buffer: float = 0.03         # 인출 시 안전 버퍼 3%
    
    # Overnight Budget (투자가능자산 대비)
    overnight_strict_max: float = 0.60   # STRICT 최대 60%
    overnight_soft_max: float = 0.15     # SOFT 최대 15%
    
    # Per-Name Caps (AUM Tier별 별도 설정 가능)
    per_name_strict_max: float = 0.15    # STRICT 종목당 15%
    per_name_soft_max: float = 0.05      # SOFT 종목당 5%
    per_name_intraday_max: float = 0.20  # Intraday 종목당 20%


@dataclass
class AllocationPlan:
    """배분 계획 출력"""
    # Sleeve 비중
    reserve_ratio: float
    alpha_ratio: float
    carry_ratio: float
    
    # Overnight 비중
    overnight_strict_ratio: float
    overnight_soft_ratio: float
    intraday_ratio: float
    
    # 종목별 타겟 비중 (AUM 대비 %)
    target_weights: Dict[str, float]
    
    # 야간 인출 플랜
    withdrawal_plan: List[Dict[str, any]]
    
    # 경고/메시지
    warnings: List[str]


class CapitalPolicy:
    """
    자본 배분 정책 엔진
    
    입력: AUM, 인출금액, 히어로 리스트
    출력: Reserve/Alpha/Carry 비중, 종목별 배분, 야간 인출 플랜
    """
    
    def __init__(self, config: CapitalPolicyConfig = None):
        self.config = config or CapitalPolicyConfig()
    
    def allocate(
        self,
        aum: float,
        withdraw_amount: float,
        heroes: List[HeroMetadata],
    ) -> AllocationPlan:
        """
        자본 배분 계산
        
        Args:
            aum: 총 자산 (AUM)
            withdraw_amount: 야간 인출 예정 금액
            heroes: 히어로 리스트 (is_hero=True만)
        
        Returns:
            AllocationPlan
        """
        warnings_list = []
        
        # 1. Reserve 계산
        reserve_ratio = self._calculate_reserve(aum, withdraw_amount, warnings_list)
        
        # 2. 투자가능자산
        investable_ratio = 1.0 - reserve_ratio
        
        # 3. 히어로 없으면 Carry로
        if not heroes:
            return AllocationPlan(
                reserve_ratio=reserve_ratio,
                alpha_ratio=0.0,
                carry_ratio=investable_ratio,
                overnight_strict_ratio=0.0,
                overnight_soft_ratio=0.0,
                intraday_ratio=0.0,
                target_weights={},
                withdrawal_plan=[],
                warnings=warnings_list + ["히어로 없음: Alpha=0, Carry로 전환"]
            )
        
        # 4. 히어로 분류 (Overnight Tier)
        strict_heroes = [h for h in heroes if h.overnight_tier == "STRICT"]
        soft_heroes = [h for h in heroes if h.overnight_tier == "SOFT"]
        intraday_heroes = [h for h in heroes if h.overnight_tier == "NONE"]
        
        # 5. Overnight 예산 계산
        overnight_strict_ratio = min(
            self.config.overnight_strict_max * investable_ratio,
            len(strict_heroes) * self.config.per_name_strict_max
        )
        
        overnight_soft_ratio = min(
            self.config.overnight_soft_max * investable_ratio,
            len(soft_heroes) * self.config.per_name_soft_max
        )
        
        # 6. Intraday 예산
        overnight_total = overnight_strict_ratio + overnight_soft_ratio
        intraday_ratio = investable_ratio - overnight_total
        
        if intraday_ratio < 0:
            warnings_list.append("Overnight 예산 초과: SOFT 축소")
            # SOFT 우선 축소
            excess = -intraday_ratio
            overnight_soft_ratio = max(0, overnight_soft_ratio - excess)
            intraday_ratio = 0
        
        # 7. 종목별 배분 (hero_score 기준)
        target_weights = self._allocate_heroes(
            strict_heroes, soft_heroes, intraday_heroes,
            overnight_strict_ratio, overnight_soft_ratio, intraday_ratio,
            aum
        )
        
        # 8. 야간 인출 플랜
        withdrawal_plan = self._plan_withdrawal(
            withdraw_amount, aum, reserve_ratio,
            strict_heroes, soft_heroes, intraday_heroes,
            target_weights
        )
        
        return AllocationPlan(
            reserve_ratio=reserve_ratio,
            alpha_ratio=investable_ratio,
            carry_ratio=0.0,  # 히어로 있으면 Carry 불필요
            overnight_strict_ratio=overnight_strict_ratio,
            overnight_soft_ratio=overnight_soft_ratio,
            intraday_ratio=intraday_ratio,
            target_weights=target_weights,
            withdrawal_plan=withdrawal_plan,
            warnings=warnings_list
        )
    
    def _calculate_reserve(
        self, aum: float, withdraw: float, warnings: List[str]
    ) -> float:
        """Reserve 비중 계산"""
        if withdraw <= 0:
            return self.config.reserve_base
        
        withdraw_ratio = withdraw / aum
        reserve_needed = withdraw_ratio + self.config.reserve_buffer
        reserve = min(self.config.reserve_max, max(self.config.reserve_base, reserve_needed))
        
        if reserve >= self.config.reserve_max:
            warnings.append(f"Reserve 상한 도달 ({reserve:.1%}): 인출금 과다")
        
        return reserve
    
    def _allocate_heroes(
        self,
        strict: List[HeroMetadata],
        soft: List[HeroMetadata],
        intraday: List[HeroMetadata],
        strict_budget: float,
        soft_budget: float,
        intraday_budget: float,
        aum: float
    ) -> Dict[str, float]:
        """종목별 타겟 비중 계산 (hero_score 기준)"""
        weights = {}
        
        # STRICT
        if strict and strict_budget > 0:
            strict_scores = [h.overnight_score for h in strict]
            total_score = sum(strict_scores)
            if total_score > 0:
                for h, score in zip(strict, strict_scores):
                    weight = (score / total_score) * strict_budget
                    weight = min(weight, self.config.per_name_strict_max)
                    weights[h.symbol] = weight
        
        # SOFT
        if soft and soft_budget > 0:
            soft_scores = [h.overnight_score if h.overnight_score > 0 else h.hero_score for h in soft]
            total_score = sum(soft_scores)
            if total_score > 0:
                for h, score in zip(soft, soft_scores):
                    weight = (score / total_score) * soft_budget
                    weight = min(weight, self.config.per_name_soft_max)
                    weights[h.symbol] = weight
        
        # Intraday
        if intraday and intraday_budget > 0:
            intraday_scores = [h.hero_score for h in intraday]
            total_score = sum(intraday_scores)
            if total_score > 0:
                for h, score in zip(intraday, intraday_scores):
                    weight = (score / total_score) * intraday_budget
                    weight = min(weight, self.config.per_name_intraday_max)
                    weights[h.symbol] = weight
        
        return weights
    
    def _plan_withdrawal(
        self,
        withdraw: float,
        aum: float,
        reserve_ratio: float,
        strict: List[HeroMetadata],
        soft: List[HeroMetadata],
        intraday: List[HeroMetadata],
        weights: Dict[str, float]
    ) -> List[Dict[str, any]]:
        """야간 인출 플랜 (청산 우선순위)"""
        if withdraw <= 0:
            return []
        
        reserve_amount = aum * reserve_ratio
        
        if withdraw <= reserve_amount:
            return [{"source": "Reserve", "amount": withdraw, "action": "현금 인출"}]
        
        # Reserve 부족: 포지션 청산 필요
        shortfall = withdraw - reserve_amount
        plan = [{"source": "Reserve", "amount": reserve_amount, "action": "Reserve 전액 사용"}]
        
        # 우선순위: SOFT → STRICT → Intraday
        for tier_name, heroes_list in [("SOFT", soft), ("STRICT", strict), ("Intraday", intraday)]:
            if shortfall <= 0:
                break
            
            for h in heroes_list:
                if shortfall <= 0:
                    break
                
                position_value = aum * weights.get(h.symbol, 0)
                liquidate = min(position_value, shortfall)
                
                plan.append({
                    "source": tier_name,
                    "symbol": h.symbol,
                    "amount": liquidate,
                    "action": f"{tier_name} 포지션 청산"
                })
                
                shortfall -= liquidate
        
        if shortfall > 0:
            plan.append({"source": "부족", "amount": shortfall, "action": "경고: 인출 불가능"})
        
        return plan


    # --- Phase 21-C: plan() for scan_heroes integration ---
    def plan(self, aum: float, heroes: Sequence[HeroMetadata]) -> pd.DataFrame:
        """
        Generate allocation plan CSV (Phase 21-C integration).
        
        Args:
            aum: Assets under management
            heroes: List of HeroMetadata (is_hero=True only)
        
        Returns:
            DataFrame with columns: symbol, sleeve, tier, weight, notional, reason
        """
        import pandas as pd
        from typing import Sequence
        
        # SSOT: No Hero = No Trade
        hero_list = [h for h in (heroes or []) if getattr(h, "is_hero", False)]
        if not hero_list:
            return pd.DataFrame([{
                "symbol": "CASH",
                "sleeve": "RESERVE",
                "tier": "NONE",
                "weight": 1.0,
                "notional": float(aum),
                "reason": "No Hero = No Trade (Alpha=0). Full reserve.",
            }])
        
        # Tier guards (STRICT gap_n>=15, SOFT gap_n>=5)
        strict_ok = [h for h in hero_list if h.overnight_tier == "STRICT" and getattr(h, "gap_n", 0) >= 15]
        soft_ok = [h for h in hero_list if h.overnight_tier == "SOFT" and getattr(h, "gap_n", 0) >= 5]
        
        # Intraday = NONE + downgraded
        intraday = []
        for h in hero_list:
            gap_n = getattr(h, "gap_n", 0) or 0
            if h.overnight_tier == "NONE":
                intraday.append(h)
            elif h.overnight_tier == "SOFT" and gap_n < 5:
                intraday.append(h)
            elif h.overnight_tier == "STRICT" and gap_n < 15:
                intraday.append(h)
        
        # Sort by score
        strict_ok.sort(key=lambda x: getattr(x, "overnight_score", 0.0) or 0.0, reverse=True)
        soft_ok.sort(key=lambda x: getattr(x, "overnight_score", 0.0) or 0.0, reverse=True)
        intraday.sort(key=lambda x: getattr(x, "hero_score", 0.0) or 0.0, reverse=True)
        
        # Budget cascade
        strict_budget = self.config.overnight_strict_max if strict_ok else 0.0
        soft_budget = self.config.overnight_soft_max if soft_ok else 0.0
        intraday_budget = 1.0 - strict_budget - soft_budget - self.config.reserve_base
        
        # Equal-weight allocation with caps
        def allocate(symbols, budget, cap):
            if not symbols or budget <= 0:
                return {}, budget
            n = len(symbols)
            per = budget / n
            if cap is None or per <= cap:
                return {s: per for s in symbols}, 0.0
            alloc = {s: cap for s in symbols}
            leftover = budget - (cap * n)
            return alloc, max(0.0, leftover)
        
        strict_alloc, strict_left = allocate(
            [h.symbol for h in strict_ok], strict_budget, self.config.per_name_strict_max
        )
        soft_alloc, soft_left = allocate(
            [h.symbol for h in soft_ok], soft_budget, self.config.per_name_soft_max
        )
        
        intraday_budget += strict_left + soft_left
        intraday_alloc, intraday_left = allocate(
            [h.symbol for h in intraday], intraday_budget, self.config.per_name_intraday_max
        )
        
        reserve_budget = self.config.reserve_base + intraday_left
        
        # Build rows
        rows = []
        tier_map = {}
        downgrade = {}
        
        for h in strict_ok:
            tier_map[h.symbol] = "STRICT"
        for h in soft_ok:
            tier_map[h.symbol] = "SOFT"
        for h in intraday:
            if h.symbol not in tier_map:
                tier_map[h.symbol] = "INTRADAY"
            if h.overnight_tier in ("SOFT", "STRICT"):
                gap_n = getattr(h, "gap_n", 0) or 0
                req = 5 if h.overnight_tier == "SOFT" else 15
                if gap_n < req:
                    downgrade[h.symbol] = f"downgraded_from={h.overnight_tier} (gap_n={gap_n}<{req})"
        
        def add_rows(alloc, tier, cap):
            for sym, w in alloc.items():
                reason = f"tier={tier}"
                if cap:
                    reason += f" cap={cap:.2f}"
                if sym in downgrade:
                    reason += f" | {downgrade[sym]}"
                rows.append({
                    "symbol": sym,
                    "sleeve": "ALPHA",
                    "tier": tier_map.get(sym, tier),
                    "weight": float(w),
                    "notional": float(w) * float(aum),
                    "reason": reason,
                })
        
        add_rows(strict_alloc, "STRICT", self.config.per_name_strict_max)
        add_rows(soft_alloc, "SOFT", self.config.per_name_soft_max)
        add_rows(intraday_alloc, "INTRADAY", self.config.per_name_intraday_max)
        
        # Reserve
        w_sum = sum(r["weight"] for r in rows)
        reserve_w = 1.0 - w_sum
        rows.append({
            "symbol": "CASH",
            "sleeve": "RESERVE",
            "tier": "RESERVE",
            "weight": float(reserve_w),
            "notional": float(reserve_w) * float(aum),
            "reason": "reserve_base + leftovers",
        })
        
        df = pd.DataFrame(rows, columns=["symbol", "sleeve", "tier", "weight", "notional", "reason"])
        df["weight"] = df["weight"].clip(lower=0.0)
        df["notional"] = df["weight"] * float(aum)
        
        return df

