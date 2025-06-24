#!/bin/bash

set -euo pipefail

ENVIRONMENT=${1:-dev}
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 必要ツールの確認
command -v docker >/dev/null || { echo "Error: docker not found"; exit 1; }
command -v aws >/dev/null || { echo "Error: aws cli not found"; exit 1; }
command -v lambroll >/dev/null || { echo "Error: lambroll not found"; exit 1; }
[[ -f "$SCRIPT_DIR/Dockerfile" ]] || { echo "Error: Dockerfile not found"; exit 1; }
[[ -f "$SCRIPT_DIR/lambroll/function.json" ]] || { echo "Error: lambroll/function.json not found"; exit 1; }

echo "Deploying Docker image..."

ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$(basename "$PWD")-${ENVIRONMENT}"
GIT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="sha-${GIT_SHA}"

echo "Image: ${ECR_REPOSITORY}:${IMAGE_TAG}"

# ECRログイン
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# Docker build & push (Lambda互換性のため --provenance=false を使用)
docker buildx build --platform linux/amd64 --provenance=false -t app:build .
docker tag app:build "${ECR_REPOSITORY}:${IMAGE_TAG}"
docker push "${ECR_REPOSITORY}:${IMAGE_TAG}"

# lambroll用環境変数設定
export FUNCTION_NAME="$(basename "$PWD")-${ENVIRONMENT}"
export IMAGE_URI="${ECR_REPOSITORY}:${IMAGE_TAG}"

# lambrollデプロイ（バージョン公開でロールバック対応）
cd lambroll && lambroll deploy --publish

echo "Deployment completed successfully!"