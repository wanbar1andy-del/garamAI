#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 8.2: 피라미딩 최적화 배치 시뮬레이션
Baseline vs Scenario A, B, C 비교
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/garam/garam")
SCRIPT = PROJECT_ROOT / "scripts/strategies/simulate_phase4_hero.py"

print("=" * 70)
print("Phase 8.2: 피라미딩 속도 최적화 - 배치 시뮬레이션")
print("=" * 70)

# 공통 설정
base_args = [
    sys.executable, str(SCRIPT),
    "--mode", "PYRAMID",
    "--weight", "0.7",
    "--aesthetic",
    "--penalty_multiplier", "0.8"
]

scenarios = [
    {
        "name": "Baseline (현재)",
        "desc": "30% 초기, 5%/10% 임계값",
        "args": base_args + [
            "--initial_weight", "0.3",
            "--thresh1", "0.05",
            "--thresh2", "0.10"
        ]
    },
    {
        "name": "Scenario A",
        "desc": "40% 초기, 5%/10% 임계값 (초기 비중만 상향)",
        "args": base_args + [
            "--initial_weight", "0.4",
            "--thresh1", "0.05",
            "--thresh2", "0.10"
        ]
    },
    {
        "name": "Scenario B",
        "desc": "30% 초기, 3%/7% 임계값 (피라미딩 속도만 상향)",
        "args": base_args + [
            "--initial_weight", "0.3",
            "--thresh1", "0.03",
            "--thresh2", "0.07"
        ]
    },
    {
        "name": "Scenario C (최적화)",
        "desc": "40% 초기, 3%/7% 임계값 (복합 최적화)",
        "args": base_args + [
            "--initial_weight", "0.4",
            "--thresh1", "0.03",
            "--thresh2", "0.07"
        ]
    }
]

for i, scenario in enumerate(scenarios, 1):
    print(f"\n[{i}/4] {scenario['name']}: {scenario['desc']}")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            scenario['args'],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        print(result.stdout)
        if result.stderr:
            print("[STDERR]", result.stderr)
        print(f"[완료] {scenario['name']} 시뮬레이션 성공")
    except subprocess.CalledProcessError as e:
        print(f"[오류] {scenario['name']} 실패: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)

print("\n" + "=" * 70)
print("배치 시뮬레이션 완료")
print("=" * 70)
print("\n다음 단계: 결과 비교 분석 (compare_scenarios.py)")
