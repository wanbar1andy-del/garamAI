"""
Garam OSS: Vertex AI Custom Training Script
- 8192-Node Brain 하이브리드 재배양 (Fine-tuning) 집행
- 사령관의 '명령 4'를 실현하기 위한 클라우드 훈련 로직
"""
import os
import argparse
from google.cloud import aiplatform

def run_vertex_training(project_id, location, bucket_name):
    aiplatform.init(project=project_id, location=location, staging_bucket=f"gs://{bucket_name}")

    # 1. 전용 훈련 이미지 (Artifact Registry에 푸시된 이미지)
    container_uri = f"gcr.io/{project_id}/garam-oss-trainer:latest"

    # 2. 하드웨어 최전선 설정 (A100-80GB 또는 L4 고성능 GPU)
    # 고성능 네트워크 및 SSD 처리량 확보를 위한 머신 타입 최적화
    machine_type = "a2-highgpu-1g" # NVIDIA A100 40GB/80GB (최고 성능 모델)
    accelerator_type = "NVIDIA_TESLA_A100"
    accelerator_count = 1

    print(f"🔥 [Vertex AI] 8192-Node '궁극의 지능' 연산 군단 기동 중... (A100 40GB)")
    
    job = aiplatform.CustomContainerTrainingJob(
        display_name="garam-oss-hyper-elite-8192",
        container_uri=container_uri,
    )

    # 명령 4 집행: 삼성전자 급등기 데이터를 활용한 파인튜닝
    # 훈련 스크립트 인자 전달
    # 3. 명령 집행: Elite AI Training Curriculum
    # train_elite_curriculum.py를 실행하여 31bp 비용과 3.0% 수익 문턱값 이식
    job.run(
        args=["python", "scripts/train_elite_curriculum.py"],
        replica_count=1,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        sync=True
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="garam-473813")
    parser.add_argument("--location", default="us-central1") # GPU 수급이 원활한 지역
    parser.add_argument("--bucket", default="garam-oss-storage")
    
    args = parser.parse_args()
    
    # run_vertex_training(args.project, args.location, args.bucket)
    print("💡 [Info] Vertex AI 훈련 스크립트가 준비되었습니다. 'gcloud' 인증 완료 후 실행 가능합니다.")
