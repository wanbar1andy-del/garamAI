"""
Garam OSS: GCP Cloud Storage Manager
- 8192-Node Brain State (2.1GB) 및 대용량 시장 데이터 동기화 관리
- 사령관의 데이터 이사를 위한 핵심 툴킷
"""
import os
import sys
from pathlib import Path

# GCP 클라우드 라이브러리 체크 및 자동 안내
try:
    from google.cloud import storage
    GCP_SDK_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    GCP_SDK_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class CloudStorageManager:
    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or os.getenv("GCP_BUCKET_NAME", "garam-oss-storage")
        self.client = None
        if GCP_SDK_AVAILABLE:
            try:
                self.client = storage.Client()
            except Exception as e:
                print(f"⚠️ GCP 인증 실패: {e}\n   'gcloud auth application-default login'이 필요할 수 있습니다.")

    def upload_brain_state(self):
        """로컬의 2.15GB Brain State를 클라우드로 이사"""
        local_path = PROJECT_ROOT / "core" / "active_config" / "neuro_brain_state.pth"
        if not local_path.exists():
            print(f"❌ [Error] 파일을 찾을 수 없습니다: {local_path}")
            return False
        
        print(f"🚀 [Migration] 8192-Node Brain 이사 중 (2.15GB)...")
        return self._upload_file(local_path, "brains/neuro_brain_state_8192.pth")

    def upload_market_data(self):
        """시장 데이터 캐시(200MB+) 이사"""
        local_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
        if not local_path.exists():
            print(f"❌ [Error] 파일을 찾을 수 없습니다: {local_path}")
            return False
            
        print(f"📊 [Migration] 시장 데이터 이사 중 (200MB+)...")
        return self._upload_file(local_path, "cache/market_matrix_8m.pkl")

    def _upload_file(self, local_path, cloud_name):
        if not GCP_SDK_AVAILABLE:
            print("❌ GCP SDK(google-cloud-storage)가 설치되지 않았습니다. 'pip install google-cloud-storage'가 필요합니다.")
            return False
            
        if not self.client:
            print("❌ GCP 클라이언트 초기화 실패. 'gcloud auth application-default login'으로 인증을 먼저 완료하십시오.")
            return False
        
        try:
            bucket = self.client.bucket(self.bucket_name)
            if not bucket.exists():
                print(f"❌ 버킷 '{self.bucket_name}'이 존재하지 않습니다. GCP 콘솔에서 먼저 생성하십시오.")
                return False
                
            blob = bucket.blob(cloud_name)
            blob.upload_from_filename(str(local_path))
            print(f"✅ 업로드 완료: gs://{self.bucket_name}/{cloud_name}")
            return True
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Garam GCP Migration Manager")
        print("Usage: python cloud_storage_manager.py [upload_brain|upload_data]")
        sys.exit(1)

    manager = CloudStorageManager()
    cmd = sys.argv[1]
    
    if cmd == "upload_brain":
        manager.upload_brain_state()
    elif cmd == "upload_data":
        manager.upload_market_data()
    else:
        print(f"Unknown command: {cmd}")
