#!/bin/bash
# HealthVault AI — Quick Re-deploy Script
# Run after pushing code updates to the server
# Usage: bash /var/www/healthvault-ai/scripts/deploy.sh

set -e  # Exit on any error

APP_DIR="/var/www/healthvault-ai"
VENV="$APP_DIR/venv"

echo "======================================"
echo " HealthVault AI — Deploying update"
echo "======================================"

# ── Pull latest code ───────────────────────────────────────────────────────────
echo "[1/5] Pulling latest code..."
cd "$APP_DIR"
git pull origin main

# ── Backend update ─────────────────────────────────────────────────────────────
echo "[2/5] Updating backend dependencies..."
source "$VENV/bin/activate"
pip install -r backend/requirements.txt --quiet
deactivate

echo "[3/5] Restarting backend..."
sudo systemctl restart healthvault-api
sudo systemctl status healthvault-api --no-pager -l

# ── Frontend update ────────────────────────────────────────────────────────────
echo "[4/5] Building frontend..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build

echo "[5/5] Restarting frontend..."
pm2 restart healthvault-app

echo ""
echo "======================================"
echo " Deploy complete!"
echo " Backend : https://api.yourdomain.com/health"
echo " Frontend: https://app.yourdomain.com"
echo "======================================"
