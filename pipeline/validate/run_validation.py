
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Setup
project_root = Path(__file__).resolve().parent.parent.parent
data_dir = project_root / "garamdata/history/minute"
files = list(data_dir.glob("*_1m.csv"))

print(f"=== 데이터 무결성 검사 (총 {len(files)}개 파일) ===")
print(f"검사 대상 경로: {data_dir}")

results = []
bad_files = []

for idx, csv_file in enumerate(files):
    try:
        df = pd.read_csv(csv_file)
        
        # 1. 컬럼 검사
        required_cols = {'date', 'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(df.columns):
            res = f"[FAIL] 컬럼 누락: {csv_file.name} ({set(df.columns)})"
            print(res)
            bad_files.append(csv_file.name)
            continue
            
        # 2. 데이터 양 검사
        if len(df) < 100:
            res = f"[WARN] 데이터 너무 적음: {csv_file.name} ({len(df)} rows)"
            print(res)
            # bad_files.append(csv_file.name) # 경고만
        
        # 3. 날짜/시간 검사
        df['dt'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
        
        # NaT 검사
        if df['dt'].isnull().any():
            res = f"[FAIL] 날짜 파싱 오류: {csv_file.name}"
            print(res)
            bad_files.append(csv_file.name)
            continue
            
        # 정렬
        df = df.sort_values('dt', ascending=True)
        
        # 기간
        start_date = df['dt'].iloc[0]
        end_date = df['dt'].iloc[-1]
        
        # 4. 결측 구간 (Gap) 검사 - 간단히 하루 이상 데이터가 비는지
        # (Trading Day 기준이 까다로우므로, 평일 기준 2일 이상 비면 경고)
        df['diff'] = df['dt'].diff()
        # 1분봉이므로 정상 차이는 1분. 장마감->개장은 큼.
        # 단순히 24시간 이상 비는 구간이 있는지 체크
        gaps = df[df['diff'] > timedelta(hours=24)]
        
        gap_info = ""
        if not gaps.empty:
            max_gap = gaps['diff'].max()
            gap_info = f" | Max Gap: {max_gap}"
            
        print(f"[OK] {csv_file.name}: {len(df):,} rows ({start_date} ~ {end_date}){gap_info}")
        
    except Exception as e:
        print(f"[ERROR] 파일 읽기 실패: {csv_file.name} - {e}")
        bad_files.append(csv_file.name)

print("\n" + "="*50)
print(f"검사 완료.")
print(f"정상 파일: {len(files) - len(bad_files)}개")
print(f"손상 파일: {len(bad_files)}개")

if bad_files:
    print("\n[손상 파일 목록 - 삭제 권장]")
    for f in bad_files:
        print(f)
else:
    print("\n✅ 모든 파일이 정상입니다!")
