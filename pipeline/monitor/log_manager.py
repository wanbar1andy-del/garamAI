
import logging
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 (c:\garam\garam)
project_root = Path(__file__).resolve().parent.parent.parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

class LogManager:
    """
    [Step 6: MONITOR]
    중앙 집중식 로깅 관리자.
    모든 파이프라인 모듈은 이 클래스를 통해 로거를 생성해야 함.
    """
    
    @staticmethod
    def get_logger(name: str):
        logger = logging.getLogger(name)
        
        # 이미 핸들러가 있다면 추가하지 않음 (중복 로그 방지)
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.DEBUG)
        
        # 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 1. 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. 파일 핸들러 (일별 로그)
        today = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(
            log_dir / f"system_{today}.log", 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

# 싱글톤 인스턴스처럼 사용 가능하지만, get_logger 메소드가 핵심
