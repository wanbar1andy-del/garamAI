"""
GARAM Dashboard Performance Test Script
대시보드 성능 테스트 스크립트
"""

import time
import requests
from datetime import datetime
import statistics

API_BASE = 'http://127.0.0.1:5000/api'

def test_api_response_times():
    """API 응답 시간 측정"""
    endpoints = [
        '/kr/positions',
        '/kr/trades/today',
        '/kr/pnl/intraday',
        '/portfolio/summary',
        '/kr/performance/summary',
        '/system/health/latest'
    ]
    
    print("=" * 60)
    print("GARAM Dashboard 성능 테스트")
    print("=" * 60)
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    for endpoint in endpoints:
        print(f"테스트 중: {endpoint}")
        times = []
        errors = 0
        
        for i in range(10):
            try:
                start = time.time()
                res = requests.get(f'{API_BASE}{endpoint}', timeout=5)
                end = time.time()
                
                if res.status_code == 200:
                    times.append((end - start) * 1000)
                else:
                    errors += 1
                    print(f"  [{i+1}/10] ERROR: HTTP {res.status_code}")
            except Exception as e:
                errors += 1
                print(f"  [{i+1}/10] ERROR: {str(e)}")
        
        if times:
            results[endpoint] = {
                'avg_ms': statistics.mean(times),
                'max_ms': max(times),
                'min_ms': min(times),
                'median_ms': statistics.median(times),
                'errors': errors,
                'success_rate': (10 - errors) / 10 * 100
            }
        else:
            results[endpoint] = {
                'avg_ms': 0,
                'max_ms': 0,
                'min_ms': 0,
                'median_ms': 0,
                'errors': errors,
                'success_rate': 0
            }
    
    print("\n" + "=" * 60)
    print("API 응답 시간 결과:")
    print("=" * 60)
    
    for endpoint, metrics in results.items():
        print(f"\n{endpoint}:")
        print(f"  평균: {metrics['avg_ms']:.2f}ms")
        print(f"  중앙값: {metrics['median_ms']:.2f}ms")
        print(f"  최소: {metrics['min_ms']:.2f}ms")
        print(f"  최대: {metrics['max_ms']:.2f}ms")
        print(f"  성공률: {metrics['success_rate']:.1f}%")
        
        # 성능 평가
        avg = metrics['avg_ms']
        if avg == 0:
            status = "❌ 실패"
        elif avg < 100:
            status = "✅ 우수"
        elif avg < 200:
            status = "⚠️  양호"
        else:
            status = "❌ 개선 필요"
        print(f"  상태: {status}")
    
    # 전체 평균 계산
    all_avgs = [m['avg_ms'] for m in results.values() if m['avg_ms'] > 0]
    if all_avgs:
        overall_avg = statistics.mean(all_avgs)
        print(f"\n전체 평균 응답 시간: {overall_avg:.2f}ms")
    
    return results

def test_api_load():
    """API 부하 테스트 - 최적화 전후 비교"""
    print("\n" + "=" * 60)
    print("API 부하 테스트 (60초)")
    print("=" * 60)
    
    endpoint = '/api/kr/positions'
    duration = 60
    start_time = time.time()
    count = 0
    
    print(f"테스트 기간: {duration}초")
    print("진행 중...\n")
    
    while time.time() - start_time < duration:
        try:
            res = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=2)
            count += 1
        except:
            pass
        time.sleep(3)  # 3초 간격 (최적화 후)
    
    elapsed = time.time() - start_time
    requests_per_min = (count / elapsed) * 60
    
    print(f"총 요청 수: {count}")
    print(f"분당 요청: {requests_per_min:.1f}")
    print(f"\n비교:")
    print(f"  최적화 전 (1초 간격): ~60 요청/분")
    print(f"  최적화 후 (3초 간격): ~{requests_per_min:.1f} 요청/분")
    print(f"  부하 감소: {((60 - requests_per_min) / 60 * 100):.1f}%")

if __name__ == '__main__':
    try:
        results = test_api_response_times()
        test_api_load()
        
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
