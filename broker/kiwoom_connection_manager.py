# -*- coding: utf-8 -*-
"""
키움 연결 관리자 (Kiwoom Connection Manager)
로그인 상태를 확인하고 관리하는 중앙 모듈

보안 중요: CommConnect()를 직접 호출하지 말 것!
이 모듈을 통해서만 키움 인스턴스를 가져와야 합니다.
"""
from pykiwoom.kiwoom import Kiwoom
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys

# Config 가져오기
try:
    from garam.config import PATHS
    KIWOOM_FLAG_PATH = PATHS.KIWOOM_FLAG_PATH
except ImportError:
    # Fallback
    KIWOOM_FLAG_PATH = Path("GARAM_Data/kiwoom_ready.flag")


class KiwoomNotLoggedInError(Exception):
    """키움이 로그인되어 있지 않을 때 발생하는 에러"""
    pass


def is_kiwoom_logged_in(max_age_seconds=120):
    """
    키움 로그인 상태 확인 (플래그 파일 기반)
    
    Args:
        max_age_seconds: 플래그 파일의 최대 허용 나이 (초)
                        기본 120초 = heartbeat 2번 누락까지 허용
    
    Returns:
        bool: 로그인되어 있으면 True, 아니면 False
    """
    try:
        if not KIWOOM_FLAG_PATH.exists():
            return False
        
        # 파일 수정 시간 확인
        mtime = KIWOOM_FLAG_PATH.stat().st_mtime
        file_age = time.time() - mtime
        
        if file_age > max_age_seconds:
            # 플래그 파일이 오래됨 (heartbeat 없음)
            return False
        
        return True
        
    except Exception as e:
        print(f"[WARNING] 플래그 파일 확인 중 에러: {e}")
        return False


def get_kiwoom_instance(check_login=True):
    """
    키움 인스턴스 반환 (CommConnect 없이)
    
    Args:
        check_login: True면 로그인 상태를 먼저 확인
    
    Returns:
        Kiwoom: 키움 객체 인스턴스
    
    Raises:
        KiwoomNotLoggedInError: 로그인되어 있지 않으면 에러
    
    주의:
        이 함수는 CommConnect()를 호출하지 않습니다.
        키움은 이미 kiwoom_login_ui.py를 통해 로그인되어 있어야 합니다.
    """
    if check_login and not is_kiwoom_logged_in():
        raise KiwoomNotLoggedInError(
            "\n" + "="*70 + "\n"
            "❌ 키움이 로그인되어 있지 않습니다!\n\n"
            "해결 방법:\n"
            "1. 먼저 키움 로그인 UI를 실행하세요:\n"
            f"   C:\\Python39-32\\python.exe scripts/kiwoom_login_ui.py\n\n"
            "2. 로그인 창에서 인증을 완료하세요\n\n"
            "3. 그 후 이 스크립트를 다시 실행하세요\n\n"
            "보안 중요: 반복 로그인은 계정 차단 위험이 있습니다.\n"
            "="*70
        )
    
    # Kiwoom 객체 생성 (CommConnect 없이)
    # 주의: 이미 다른 프로세스(login_ui)에서 로그인되어 있으므로
    # 새 인스턴스도 같은 로그인 세션을 공유합니다 (COM 특성)
    kiwoom = Kiwoom()
    
    # 연결 상태 확인 (실제 API 호출)
    try:
        state = kiwoom.GetConnectState()
        if state != 1:
            raise KiwoomNotLoggedInError(
                "\n" + "="*70 + "\n"
                "❌ 키움 연결 상태 확인 실패 (GetConnectState != 1)\n\n"
                "가능한 원인:\n"
                "1. kiwoom_login_ui.py가 실행 중이지 않음\n"
                "2. 로그인이 만료됨\n"
                "3. 키움 OpenAPI 프로그램 문제\n\n"
                "해결: kiwoom_login_ui.py를 다시 실행하세요\n"
                "="*70
            )
    except Exception as e:
        raise KiwoomNotLoggedInError(
            f"\n" + "="*70 + "\n"
            f"❌ 키움 API 호출 중 에러: {e}\n\n"
            "키움 OpenAPI가 정상적으로 설치되어 있는지 확인하세요.\n"
            "="*70
        )
    
    return kiwoom


def wait_for_login(timeout=300, check_interval=5):
    """
    키움 로그인을 기다림
    
    Args:
        timeout: 최대 대기 시간 (초)
        check_interval: 확인 간격 (초)
    
    Returns:
        bool: 로그인 성공하면 True, 타임아웃되면 False
    """
    start_time = time.time()
    
    print(f"키움 로그인 대기 중... (최대 {timeout}초)")
    print("kiwoom_login_ui.py를 실행하고 로그인하세요.")
    
    while time.time() - start_time < timeout:
        if is_kiwoom_logged_in():
            print("✓ 키움 로그인 확인!")
            return True
        
        remaining = int(timeout - (time.time() - start_time))
        print(f"대기 중... (남은 시간: {remaining}초)", end='\r')
        time.sleep(check_interval)
    
    print("\n✗ 타임아웃: 로그인이 완료되지 않았습니다.")
    return False


def get_login_info():
    """
    현재 로그인 정보 반환
    
    Returns:
        dict: 사용자 정보 (user_id, user_name, accounts 등)
        None: 로그인되어 있지 않으면
    """
    try:
        if not is_kiwoom_logged_in():
            return None
        
        kiwoom = get_kiwoom_instance(check_login=False)
        
        return {
            'user_id': kiwoom.GetLoginInfo("USER_ID"),
            'user_name': kiwoom.GetLoginInfo("USER_NAME"),
            'accounts': kiwoom.GetLoginInfo("ACCNO"),
            'server_type': kiwoom.GetLoginInfo("GetServerGubun"),
            'flag_path': str(KIWOOM_FLAG_PATH),
            'flag_age': int(time.time() - KIWOOM_FLAG_PATH.stat().st_mtime) if KIWOOM_FLAG_PATH.exists() else None
        }
    except Exception as e:
        print(f"로그인 정보 가져오기 실패: {e}")
        return None


# ========== 재발 방지: CommConnect 직접 호출 차단 ==========

def block_direct_connect():
    """
    CommConnect 직접 호출을 차단하는 monkey patch
    
    사용법:
        from broker.kiwoom_connection_manager import block_direct_connect
        block_direct_connect()  # 스크립트 시작 시 호출
    """
    original_connect = Kiwoom.CommConnect
    
    def blocked_connect(self, *args, **kwargs):
        raise RuntimeError(
            "\n" + "="*70 + "\n"
            "🚫 커넥션 보안 위반!\n\n"
            "CommConnect()를 직접 호출할 수 없습니다!\n\n"
            "올바른 방법:\n"
            "  from broker.kiwoom_connection_manager import get_kiwoom_instance\n"
            "  kiwoom = get_kiwoom_instance()\n\n"
            "이유: 반복 로그인은 보안 위험이 있으며 계정 차단될 수 있습니다.\n"
            "="*70
        )
    
    Kiwoom.CommConnect = blocked_connect
    print("[보안] CommConnect() 직접 호출이 차단되었습니다.")


if __name__ == "__main__":
    """테스트 및 상태 확인"""
    print("="*70)
    print("키움 연결 관리자 - 상태 확인")
    print("="*70)
    
    # 로그인 상태 확인
    logged_in = is_kiwoom_logged_in()
    print(f"\n로그인 상태: {'✓ 로그인됨' if logged_in else '✗ 로그인 안 됨'}")
    
    if logged_in:
        info = get_login_info()
        if info:
            print(f"\n사용자 정보:")
            print(f"  - 사용자 ID: {info['user_id']}")
            print(f"  - 이름: {info['user_name']}")
            print(f"  - 계좌: {info['accounts']}")
            print(f"  - 서버: {'모의투자' if info['server_type'] == '1' else '실서버'}")
            print(f"  - 플래그 나이: {info['flag_age']}초")
        
        # 인스턴스 가져오기 테스트
        try:
            kiwoom = get_kiwoom_instance()
            print("\n✓ 키움 인스턴스 가져오기 성공!")
        except Exception as e:
            print(f"\n✗ 키움 인스턴스 가져오기 실패: {e}")
    else:
        print("\n해결 방법:")
        print("  C:\\Python39-32\\python.exe scripts/kiwoom_login_ui.py")
    
    print("\n" + "="*70)
