#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
PACKAGE_NAME="slack-bot-lambda.zip"
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Check requirements
command -v uv >/dev/null || { echo "Error: uv not found"; exit 1; }
command -v lambroll >/dev/null || { echo "Error: lambroll not found"; exit 1; }
[[ -f "$SCRIPT_DIR/requirements.txt" ]] || { echo "Error: requirements.txt not found"; exit 1; }
[[ -d "$SCRIPT_DIR/src" ]] || { echo "Error: src directory not found"; exit 1; }
[[ -f "$SCRIPT_DIR/function.json" ]] || { echo "Error: function.json not found"; exit 1; }

echo "Building Lambda package..."

# Setup virtual environment
cd "$SCRIPT_DIR"
uv venv --python 3.13 --quiet
uv sync --quiet
source .venv/bin/activate

# Install pip in the virtual environment
python -m ensurepip --upgrade

# Build
mkdir -p "$BUILD_DIR"
cp -r "$SCRIPT_DIR/src"/* "$TEMP_DIR/"

# Install dependencies using uv export with platform specification
python -m pip install \
    --no-cache-dir \
    --no-deps \
    -r <(uv export --format requirements-txt --no-dev --no-hashes | grep -vP "(botocore|tzdata)") \
    --target "$TEMP_DIR/" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all:

# Cleanup
find "$TEMP_DIR" -type f -name "*.pyc" -delete
find "$TEMP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -name "*.so" -exec strip {} + 2>/dev/null || true

# Create ZIP
cd "$TEMP_DIR"
zip -r "$BUILD_DIR/$PACKAGE_NAME" . -x "*__pycache__*" -q

echo "Built: $BUILD_DIR/$PACKAGE_NAME"

# Deploy with lambroll
echo "Deploying with lambroll..."
cd "$SCRIPT_DIR"
lambroll deploy --src "$BUILD_DIR/$PACKAGE_NAME"

echo "Deployment completed successfully!"