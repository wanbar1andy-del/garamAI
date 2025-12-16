"""
Garam 프로젝트 전체 검증 마스터 스크립트
모든 테스트를 순차적으로 실행하고 종합 보고서를 생성합니다.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_test(script_name, description):
    """테스트 스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"실행 중: {description}")
    print(f"스크립트: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            encoding='cp949',  # Windows 한글 지원
            errors='replace',  # 디코딩 오류 시 대체 문자 사용
            timeout=60
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n[OK] {description} 성공!")
            return True, result.stdout or ""
        else:
            print(f"\n[FAIL] {description} 실패!")
            if result.stderr:
                print(f"에러: {result.stderr}")
            return False, result.stdout or ""
            
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {description} 타임아웃 (60초 초과)")
        return False, ""
    except Exception as e:
        print(f"\n[ERROR] {description} 실행 중 오류: {e}")
        return False, ""

def main():
    """전체 검증 실행"""
    start_time = datetime.now()
    
    print("=" * 60)
    print("Garam 프로젝트 전체 검증 시작")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("validate_garam.py", "프로젝트 구조 검증"),
        ("test_components.py", "컴포넌트 단위 테스트"),
        ("test_integration.py", "통합 백테스트 테스트"),
        ("test_filesystem.py", "파일 시스템 접근성 테스트"),
        ("alpha_lab/regime/test_regime.py", "Regime Engine Tests"),
        ("alpha_lab/risk/test_risk_engine.py", "Risk Engine Tests"),
        ("alpha_lab/brain/test_surfing_brain.py", "Surfing Brain Tests"),
    ]
    
    results = []
    outputs = []
    
    for script, description in tests:
        success, output = run_test(script, description)
        results.append((description, success))
        outputs.append((description, output))
    
    # 종합 결과
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("전체 검증 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "[OK] 통과" if success else "[FAIL] 실패"
        print(f"{description:30s}: {status}")
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과")
    print(f"소요 시간: {duration:.1f}초")
    print(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 상세 보고서 생성
    report_file = Path("test_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Garam 프로젝트 전체 검증 보고서\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"실행 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"소요 시간: {duration:.1f}초\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("요약\n")
        f.write("=" * 60 + "\n")
        f.write(f"총 테스트: {total}개\n")
        f.write(f"통과: {passed}개\n")
        f.write(f"실패: {total - passed}개\n")
        f.write(f"성공률: {passed/total*100:.1f}%\n\n")
        
        for description, success in results:
            status = "[OK] 통과" if success else "[FAIL] 실패"
            f.write(f"{description:30s}: {status}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("상세 결과\n")
        f.write("=" * 60 + "\n\n")
        
        for description, output in outputs:
            f.write(f"\n{'='*60}\n")
            f.write(f"{description}\n")
            f.write(f"{'='*60}\n")
            f.write(output)
            f.write("\n")
    
    print(f"\n📄 상세 보고서 생성: {report_file.absolute()}")
    
    # 최종 판정
    if passed == total:
        print("\n" + "=" * 60)
        print("[SUCCESS] 모든 검증 테스트가 성공했습니다!")
        print("Garam 프로젝트는 완벽하게 작동합니다!")
        print("=" * 60)
        return 0
    else:
        print(f"\n[WARNING] {total - passed}개 테스트에 문제가 있습니다.")
        print("상세 내용은 test_report.txt를 확인하세요.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
