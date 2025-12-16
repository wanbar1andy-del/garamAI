"""
Health Service - Independent Health Monitoring Service
실행 방법:
1. 단발: python health_service.py --once
2. 데몬: python health_service.py (5분마다 반복)
3. Task Scheduler: schtasks /create /tn "GARAM Health" /tr "python c:\garam\garam\health_service.py --once" /sc minute /mo 5
"""
import sys
sys.path.insert(0, 'c:/garam')

from garam.core.health_collector import get_health_collector
import time
import logging
import argparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('c:/garam/garam/GARAM_Data/logs/health_service.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='GARAM Health Monitoring Service')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=300, help='Interval in seconds (default: 300)')
    args = parser.parse_args()

    collector = get_health_collector()
    
    if args.once:
        logger.info("Running health check once...")
        collector.collect_and_save()
        logger.info("✅ Health check complete")
    else:
        logger.info(f"Starting health service (interval: {args.interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                collector.collect_and_save()
                logger.info(f"Health check complete, sleeping {args.interval}s...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Health service stopped by user")

if __name__ == '__main__':
    main()
