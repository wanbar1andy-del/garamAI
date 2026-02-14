# Phase 24 SSOT — Intraday Hero & Switching Research

## 목적

- 10분/30분/60분 스케일에서 "히어로가 존재했는가"를 오라클로 라벨링한다.
- 엔진(Phase 23 Sealed Champion)이 그 히어로를 얼마나 포착했는지(Selection Quality)를 계량한다.
- "언제 갈아타야 하는가"를 스위칭 규칙 후보로 실험하고, 시간 스케일 확장 시 성과 하락 원인을 분해한다.

## SSOT 비용(봉인)

- Roundtrip Cost = 30.0 bps
  - Slippage 3.5bps/side * 2
  - Fee 1.5bps/side * 2
  - Tax 20.0bps(Exit)
- 오라클/리포트에서는 net_ret = raw_ret - 0.0030 (근사) 사용

## 앵커(Decision Grid)

- Anchor frequency: 5분(기본), 옵션 10분
- Session: 09:05 ~ 15:10 (기본)
- Horizons(H): 10, 30, 60 minutes (기본)
- Top-K: 5 (기본)

## 오라클 라벨 정의

- 각 anchor ts에서 모든 종목의 forward return(H)을 계산
- raw_ret = close(ts+H)/close(ts) - 1
- net_ret = raw_ret - 0.0030
- OracleTop1(ts,H) = max(net_ret)
- HeroExists(ts,H,thr) = OracleTop1(ts,H) >= thr
  - thr 기본 0.0 또는 +0.2% 등 실험

## 엔진 선택 품질(Selection Quality)

- Decision Tape: ts별로 엔진이 "후보로 인정"한 종목(Phase23의 EntryGate + Score)을 랭킹 기록
- PolicyTop1Ret(ts,H): Tape rank1의 net_ret
- PolicyBestOf3Ret(ts,H): rank1~3 중 최대 net_ret
- Regret(ts,H) = OracleTop1(ts,H) - PolicyBestOf3Ret(ts,H)

## 레짐(상승/보합/하락) 분류(인트라데이)

- Market proxy: 005930(또는 universe 평균) 60분 수익률 r_mkt_60
- UP: r_mkt_60 >= +0.20%
- DOWN: r_mkt_60 <= -0.20%
- FLAT: 그 외

## 핵심 산출물

1) Oracle Labels (ts, symbol, H, raw_ret, net_ret, rank)
2) Decision Tape (ts, symbol, score, rank, pass_gate, roc_5m, vol_accel, rev_flags, ma60)
3) Regret Report (ts별 OracleTop1 vs PolicyBestOf3, 레짐별 집계)
4) Switching Sandbox (후보 규칙별 성과/회전율/비용 민감도)

## 5일 내 파라미터 캘리브레이션 원칙 (가람 기준)

- 1~5일 샘플에서 "히어로 존재성/포착률/리그렛"이 답을 준다.
- 그 다음 1개월/6개월은 '드리프트/레짐 혼합 내구성' 검증이다.
