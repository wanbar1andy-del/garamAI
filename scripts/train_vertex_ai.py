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

    # 2. 하드웨어 최전선 설정 (A100-80GB - 궁극의 지능용)
    # 64K 노드 시뮬레이션 및 훈련을 위해 최고 성능의 GPU 자산 투입
    machine_type = "a2-ultragpu-1g" # NVIDIA A100 80GB (64K 수용 가능 모델)
    accelerator_type = "NVIDIA_TESLA_A100"
    accelerator_count = 1

    print(f"🔥 [Vertex AI] 65,536-Node '궁극의 포식자' 고차원 연산 군단 기동 중... (A100 80GB)")
    
    job = aiplatform.CustomContainerTrainingJob(
        display_name="garam-oss-ultimate-predator-64k",
        container_uri=container_uri,
    )

    # 3. 명령 집행: Ultimate 64K Training
    # train_ultimate_64k.py를 실행하여 65,536 노드 지능 폭발 집행
    job.run(
        args=["python", "scripts/train_ultimate_64k.py"],
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
