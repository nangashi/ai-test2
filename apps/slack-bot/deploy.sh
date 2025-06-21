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

# Build
mkdir -p "$BUILD_DIR"
cp -r "$SCRIPT_DIR/src" "$TEMP_DIR/"

# Install dependencies
VENV_DIR="$TEMP_DIR/venv"
uv venv "$VENV_DIR" --python 3.11 --quiet
uv pip install --python "$VENV_DIR/bin/python" --requirement "$SCRIPT_DIR/requirements.txt" --quiet

# Copy packages
SITE_PACKAGES="$VENV_DIR/lib/python3.11/site-packages"
cp -r "$SITE_PACKAGES"/* "$TEMP_DIR/"

# Cleanup
find "$TEMP_DIR" -type f -name "*.pyc" -delete
find "$TEMP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -name "*.so" -exec strip {} + 2>/dev/null || true
rm -rf "$VENV_DIR"

# Create ZIP
cd "$TEMP_DIR"
zip -r "$BUILD_DIR/$PACKAGE_NAME" . -q

echo "Built: $BUILD_DIR/$PACKAGE_NAME"

# Deploy with lambroll
echo "Deploying with lambroll..."
cd "$SCRIPT_DIR"
lambroll deploy --src "$BUILD_DIR/$PACKAGE_NAME"

echo "Deployment completed successfully!"