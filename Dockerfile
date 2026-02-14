# Garam OSS: GCP Migration Dockerfile
# GPU 가속을 위한 NVIDIA CUDA 베이스 이미지 사용
FROM nvidia/cuda:12.4.1-base-ubuntu22.04

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    google-cloud-storage \
    google-cloud-aiplatform \
    scikit-learn \
    pyyaml \
    pathlib

# 프로젝트 파일 복사
COPY . .

# GCP 환경변수 설정 (기본값)
ENV PYTHONUNBUFFERED=1
ENV GCP_PROJECT_ID="garam-437813"
ENV GCP_BUCKET_NAME="garam-oss-storage"

# 진입점 설정 (기본적으로 추론 테스트 실행 가능)
CMD ["python3", "scripts/test_oss_inference.py"]
