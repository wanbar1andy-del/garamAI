"""
Turbo Overlay Manager
Base 포트폴리오에 선택적 레버리지 추가
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger("TurboOverlay")

class TurboOverlayManager:
    """
    Turbo Overlay 관리
    
    역할:
    - Base 포트폴리오 종목과 동일하게 진입
    - 2종목 보유 시에만 활성화
    - 2.5x 레버리지 적용
    - 독립적인 Exit 전략 (트레일링 스탑)
    - 수익의 90% 재투입
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        
        # 레버리지 설정 (Base와 동일한 예산 사용)
        self.turbo_multiplier = config.get('turbo_multiplier', 2.5)
        self.per_symbol_cap = config.get('per_symbol_cap', 3.0)
        self.total_cap = config.get('total_cap', 3.0)
        
        # Exit 설정 (V2: Smart Exit/Re-entry)
        self.daily_decline_exit = config.get('daily_decline_exit', 0.03)  # 일간 -3% 하락 시 Exit
        self.consecutive_decline_exit = config.get('consecutive_decline_exit', 0.04)  # 3일 합 -4%
        self.trailing_stop_pct = config.get('trailing_stop_pct', 0.05)  # 기본 5%
        self.tight_trailing_pct = config.get('tight_trailing_pct', 0.03)  # 2.5x 구간용 3%
        self.portfolio_dd_stop = config.get('portfolio_dd_stop', 0.18)  # 포트폴리오 DD 18%
        
        # 재진입 설정 (V2)
        self.reentry_cooldown_days = config.get('reentry_cooldown_days', 3)  # 3일 쿨다운
        self.reentry_recovery_ratio = config.get('reentry_recovery_ratio', 0.5)  # DD 50% 회복
        self.reentry_momentum_threshold = config.get('reentry_momentum_threshold', 0.03)  # 2-3일 합 3%
        self.reentry_daily_threshold = config.get('reentry_daily_threshold', 0.02)  # 당일 2%
        self.min_concentration_reentry = config.get('min_concentration_reentry', 0.8)  # 최소 집중도
        
        self.allowed_regimes = config.get('allowed_regimes', 
                                         ['R1_STRONG_UP', 'R2_UP'])
        
        # Turbo 포지션 추적
        self.turbo_positions = {}  # {symbol: {'entry_price', 'high', 'qty', 'entry_date'}}
        self.is_active = False
        self.last_regime = None
        self.previous_position_count = 0
        
        # NEW V1.1: 포트폴리오 레벨 DD 추적
        self.portfolio_high = 0  # Turbo equity 최고점
        self.current_multiplier = 1.0  # 현재 적용 중인 multiplier
        
        # 통계 (수익 재투입 없음 - Base equity 사용)
        self.total_trades = 0
        self.winning_trades = 0
        
        logger.info(f"TurboOverlayManager Initialized (Enabled: {self.enabled})")
        logger.info(f"  Multiplier: {self.turbo_multiplier}x (Base budget 사용)")
        logger.info(f"  Trailing Stop: {self.trailing_stop_pct:.1%} (일반) / {self.tight_trailing_pct:.1%} (2.5x)")
        logger.info(f"  Portfolio DD Stop: {self.portfolio_dd_stop:.1%}")
    
    def should_activate(self, base_positions: Dict, regime: str, 
                       cash: float, total_equity: float) -> bool:
        """
        Turbo 활성화 조건 체크
        """
        if not self.enabled:
            return False
        
        # Rule 1: 최소 1종목 이상
        if len(base_positions) < 1:
            return False
        
        # Rule 2: 상승 Regime
        if regime not in self.allowed_regimes:
            return False
        
        # Rule 3: 현금 비중 충분 (최소 10% - 레버리지 고려)
        cash_ratio = cash / total_equity if total_equity > 0 else 0
        min_cash = 0.10  # 10%
        if cash_ratio < min_cash:
            logger.warning(f"⚠️ Cash ratio too low: {cash_ratio:.1%} < {min_cash:.1%}")
            return False
        
        return True
    
    def calculate_concentration_ratio(self, base_weights: Dict[str, float]) -> float:
        """
        포트폴리오 집중도 계산
        
        Returns:
            concentration: 0.0 ~ 1.0 (1.0 = 완전 집중, 0.0 = 완전 분산)
        """
        if not base_weights:
            return 0.0
        
        # 비중 정렬 (큰 순서)
        sorted_weights = sorted(base_weights.values(), reverse=True)
        
        if len(sorted_weights) == 1:
            return 1.0  # 1종목 = 완전 집중
        elif len(sorted_weights) == 2:
            return 1.0  # 2종목 = 최대 집중
        else:
            # Top 2 종목의 비중 합
            top2_weight = sum(sorted_weights[:2])
            total_weight = sum(sorted_weights)
            
            # 집중도 = Top2 비중 / 전체 비중
            concentration = top2_weight / total_weight if total_weight > 0 else 0.0
            
            return concentration
    
    def get_turbo_multiplier(self, concentration: float) -> float:
        """
        집중도에 따른 Turbo multiplier 계산
        
        Args:
            concentration: 0.0 ~ 1.0
            
        Returns:
            multiplier: 1.0 ~ 2.5
            
        Examples:
            concentration 1.0 (2종목) → 2.5x
            concentration 0.7 (5종목, top2=70%) → 1.75x
            concentration 0.5 (분산) → 1.25x
        """
        # 선형 보간: concentration 0.5 → 1.0x, 1.0 → 2.5x
        min_concentration = 0.5  # 이하는 Turbo 비활성
        max_multiplier = self.turbo_multiplier  # 2.5
        
        if concentration < min_concentration:
            return 1.0  # No turbo
        
        # 선형 보간
        # concentration 0.5 → 1.0x
        # concentration 1.0 → 2.5x
        multiplier = 1.0 + (max_multiplier - 1.0) * ((concentration - min_concentration) / (1.0 - min_concentration))
        
        return multiplier
    
    def apply_overlay(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Base weights에 Turbo overlay 적용 (집중도 기반)
        
        Args:
            base_weights: {symbol: weight} Base 1.0x 비중
            
        Returns:
            final_weights: {symbol: weight} Turbo 적용 최종 비중
        """
        if not self.is_active:
            return base_weights  # Turbo 비활성 시 Base 그대로
        
        # 집중도 계산
        concentration = self.calculate_concentration_ratio(base_weights)
        
        # 집중도 기반 multiplier
        multiplier = self.get_turbo_multiplier(concentration)
        
        if multiplier <= 1.0:
            logger.info(f"📊 Concentration too low ({concentration:.1%}) - No Turbo")
            return base_weights
        
        final_weights = {}
        
        for sym, base_weight in base_weights.items():
            # Turbo 적용
            turbo_weight = base_weight * multiplier
            
            # 종목별 한도
            capped_weight = min(turbo_weight, self.per_symbol_cap)
            
            final_weights[sym] = capped_weight
        
        # 총 노출 한도
        total_exposure = sum(final_weights.values())
        if total_exposure > self.total_cap:
            scale = self.total_cap / total_exposure
            final_weights = {sym: w * scale for sym, w in final_weights.items()}
            logger.warning(f"⚠️ Turbo total exposure capped: "
                          f"{total_exposure:.2f}x → {self.total_cap:.2f}x")
        
        logger.info(f"🔥 Turbo Overlay: Concentration {concentration:.1%} → "
                   f"Multiplier {multiplier:.2f}x → "
                   f"Exposure {sum(final_weights.values()):.2f}x")
        
        # V1.1: 현재 multiplier 저장
        self.current_multiplier = multiplier
        
        return final_weights
    
    
    def check_exit_conditions(self, current_prices: Dict[str, float], 
                              regime: str, position_count: int,
                              turbo_equity: float = None,
                              daily_return: float = 0.0) -> bool:
        """
        Turbo Exit 조건 체크 (V2: Daily Decline + Consecutive Decline + Portfolio DD)
        
        Returns:
            bool: True if should exit turbo positions
        """
        if not self.is_active:
            return False
        
        # V2 Exit 조건 1: 단일일 급락 (-3%)
        if self.current_multiplier >= 2.0 and daily_return <= -self.daily_decline_exit:
            logger.warning(f"🚨 Turbo Exit (Daily Decline): {daily_return:.2%} <= -{self.daily_decline_exit:.1%}")
            self.exit_count += 1
            return True
        
        # V2 Exit 조건 2: 연속 하락 (3일 합 -4%)
        self.recent_returns.append(daily_return)
        if len(self.recent_returns) > 3:
            self.recent_returns.pop(0)
        
        if self.current_multiplier >= 2.0 and len(self.recent_returns) >= 3:
            sum_3d = sum(self.recent_returns)
            if sum_3d <= -self.consecutive_decline_exit:
                logger.warning(f"🚨 Turbo Exit (3-day Decline): {sum_3d:.2%} <= -{self.consecutive_decline_exit:.1%}")
                self.exit_count += 1
                return True
        
        # V1.1 Exit 조건 3: 포트폴리오 DD
        if turbo_equity is not None:
            if turbo_equity > self.portfolio_high:
                self.portfolio_high = turbo_equity
            
            portfolio_dd = (turbo_equity - self.portfolio_high) / self.portfolio_high if self.portfolio_high > 0 else 0
            
            if portfolio_dd <= -self.portfolio_dd_stop:
                logger.warning(f"🚨 Turbo Exit (Portfolio DD): {portfolio_dd:.2%} < -{self.portfolio_dd_stop:.1%}")
                self.exit_count += 1
                return True
        
        # Exit 조건 4: Trailing Stop (가변)
        trailing_threshold = self.tight_trailing_pct if self.current_multiplier >= 2.0 else self.trailing_stop_pct
        
        for symbol, pos in self.turbo_positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            if current_price > pos['high']:
                pos['high'] = current_price
            
            drawdown = (current_price - pos['high']) / pos['high']
            
            if drawdown <= -trailing_threshold:
                logger.info(f"🚨 Turbo Exit (Trailing Stop {trailing_threshold:.1%}): {symbol} DD {drawdown:.2%}")
                self.exit_count += 1
                return True
        
        # Exit 조건 5: Regime 전환
        if (self.last_regime in self.allowed_regimes and 
            regime not in self.allowed_regimes):
            logger.info(f"🚨 Turbo Exit (Regime Change): {self.last_regime} → {regime}")
            self.exit_count += 1
            return True
        
        # Exit 조건 6: 포지션 수 변경
        if (self.previous_position_count == 2 and 
            position_count != 2):
            logger.info(f"🚨 Turbo Exit (Position Count): 2 → {position_count}")
            self.exit_count += 1
            return True
        
        return False

    
    def enter_turbo(self, positions: Dict, entry_prices: Dict):
        """
        Turbo 포지션 진입 기록
        """
        self.is_active = True
        self.turbo_positions = {}
        
        for symbol in positions:
            entry_price = entry_prices.get(symbol, 0)
            self.turbo_positions[symbol] = {
                'entry_price': entry_price,
                'high': entry_price,
                'qty': positions[symbol].get('qty', 0),
                'entry_date': datetime.now().strftime('%Y-%m-%d')
            }
        
        logger.info(f"🔥 Turbo ENTER: {list(self.turbo_positions.keys())}")
    
    def exit_turbo(self, exit_prices: Dict) -> float:
        """
        Turbo 포지션 청산 및 손익 계산
        
        Returns:
            realized_pnl: 실현 손익
        """
        realized_pnl = 0
        
        for symbol, pos in self.turbo_positions.items():
            if symbol not in exit_prices:
                continue
            
            exit_price = exit_prices[symbol]
            entry_price = pos['entry_price']
            qty = pos['qty']
            
            pnl = (exit_price - entry_price) * qty
            realized_pnl += pnl
            
            logger.info(f"  {symbol}: Entry {entry_price:,.0f} → "
                       f"Exit {exit_price:,.0f}, "
                       f"PnL {pnl:,.0f} KRW")
        
        # 손익 처리
        self.process_pnl(realized_pnl)
        
        # 초기화
        self.is_active = False
        self.turbo_positions = {}
        
        logger.info(f"🚨 Turbo EXIT: Total PnL {realized_pnl:,.0f} KRW")
        
        return realized_pnl
    
    def process_pnl(self, realized_pnl: float):
        """
        Turbo 거래 통계 기록 (수익은 Base equity에 자동 반영)
        """
        self.total_trades += 1
        if realized_pnl > 0:
            self.winning_trades += 1
            logger.info(f"✅ Turbo Profit: {realized_pnl:,.0f} KRW")
        else:
            logger.warning(f"❌ Turbo Loss: {realized_pnl:,.0f} KRW")
        
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        logger.info(f"   Turbo Stats: {self.winning_trades}/{self.total_trades} trades (Win Rate: {win_rate:.1%})")
    
    def get_status(self) -> Dict:
        """
        Turbo 상태 정보 반환
        """
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        return {
            'enabled': self.enabled,
            'is_active': self.is_active,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'position_count': len(self.turbo_positions),
            'positions': list(self.turbo_positions.keys())
        }
