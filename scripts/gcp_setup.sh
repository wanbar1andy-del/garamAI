#!/bin/bash
# Garam OSS: GCP 요새 구축 스크립트 (Command 1)
# 8192-Node 지능의 본부를 GCP Compute Engine에 건설한다.

set -e

echo "🏛️ [GCP Setup] Garam OSS 요새 구축 시작..."

# 1. 시스템 업데이트 및 필수 패키지 설치
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python3-pip python3-venv wget nvidia-driver-535

# 2. CUDA 12.4 설치 (필요시)
if ! command -v nvcc &> /dev/null
then
    echo "⚙️ [Setup] CUDA 12.4 설치 중..."
    wget https://developer.download.nvidia.com/compute/cuda/12.4.1/local_installers/cuda_12.4.1_550.54.15_linux.run
    sudo sh cuda_12.4.1_550.54.15_linux.run --silent --toolkit
fi

# 3. Garam 프로젝트 복제 및 환경 설정
PROJECT_DIR="garam"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "⚔️ [Setup] 프로젝트 무기고 동기화 (GitHub)..."
    git clone https://github.com/wanbar1andy-del/garamAI.git $PROJECT_DIR
fi

cd $PROJECT_DIR
git checkout phase3-refactor

# 4. Python 가상환경 및 의존성 설치
echo "🐍 [Setup] Python 지능 환경 구성 중..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

# 5. GCS 연결 확인
echo "☁️ [Setup] 클라우드 금고(GCS) 연결 준비..."
pip install google-cloud-storage google-cloud-aiplatform

echo "✅ [SUCCESS] 가람 2.2 GCP 요새 구축 완료!"
echo "명령 3(Brain Transfer)을 통해 지능 본체를 이식하십시오."
