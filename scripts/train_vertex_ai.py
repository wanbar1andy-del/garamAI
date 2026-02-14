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

    # 2. 하드웨어 설정 (사령관의 야전 지휘소보다 강력한 L4 GPU)
    machine_type = "g2-standard-4"
    accelerator_type = "NVIDIA_L4"
    accelerator_count = 1

    print(f"🔥 [Vertex AI] 8192-Node 지능 재배양 임무 생성 중...")
    
    job = aiplatform.CustomContainerTrainingJob(
        display_name="garam-oss-finetuning-8192",
        container_uri=container_uri,
    )

    # 명령 4 집행: 삼성전자 급등기 데이터를 활용한 파인튜닝
    # 훈련 스크립트 인자 전달
    job.run(
        args=["--mode", "FINETUNE", "--target", "005930", "--epochs", "10"],
        replica_count=1,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        sync=True
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="garam-437813")
    parser.add_argument("--location", default="us-central1") # GPU 수급이 원활한 지역
    parser.add_argument("--bucket", default="garam-oss-storage")
    
    args = parser.parse_args()
    
    # run_vertex_training(args.project, args.location, args.bucket)
    print("💡 [Info] Vertex AI 훈련 스크립트가 준비되었습니다. 'gcloud' 인증 완료 후 실행 가능합니다.")
