#!/usr/bin/env bash
# Render.com build script — installs system packages + Python deps
set -e

echo "=== Installing system dependencies ==="
apt-get update -y -q
apt-get install -y -q tesseract-ocr poppler-utils libgl1

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Build complete ==="
