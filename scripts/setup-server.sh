#!/bin/bash
# HealthVault AI — One-time Server Setup Script
# Run ONCE on a fresh Ubuntu 22.04 server as root or sudo user
# Usage: sudo bash setup-server.sh

set -e

DOMAIN="yourdomain.com"       # ← CHANGE THIS
APP_USER="www-data"
APP_DIR="/var/www/healthvault-ai"

echo "======================================"
echo " HealthVault AI — Server Setup"
echo "======================================"

# ── 1. System update ───────────────────────────────────────────────────────────
echo "[Step 1] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── 2. Install system dependencies ────────────────────────────────────────────
echo "[Step 2] Installing dependencies..."
apt-get install -y \
    nginx \
    python3.11 python3.11-venv python3-pip python3.11-dev \
    tesseract-ocr tesseract-ocr-eng \
    libpq-dev gcc \
    mupdf-tools poppler-utils \
    git curl wget unzip \
    certbot python3-certbot-nginx \
    ufw fail2ban

# ── 3. Install Node.js 20 LTS ─────────────────────────────────────────────────
echo "[Step 3] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g pm2

# ── 4. Firewall ────────────────────────────────────────────────────────────────
echo "[Step 4] Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── 5. Log directory ──────────────────────────────────────────────────────────
echo "[Step 5] Creating log directory..."
mkdir -p /var/log/healthvault
chown -R $APP_USER:$APP_USER /var/log/healthvault

# ── 6. App directory ──────────────────────────────────────────────────────────
echo "[Step 6] Creating app directory..."
mkdir -p "$APP_DIR"
chown -R $APP_USER:$APP_USER "$APP_DIR"

# ── 7. Nginx site configs ─────────────────────────────────────────────────────
echo "[Step 7] Configuring Nginx..."
cp "$APP_DIR/nginx/api.conf" /etc/nginx/sites-available/healthvault-api
cp "$APP_DIR/nginx/app.conf" /etc/nginx/sites-available/healthvault-app

# Replace placeholder domain
sed -i "s/yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/healthvault-api
sed -i "s/yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/healthvault-app

ln -sf /etc/nginx/sites-available/healthvault-api /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/healthvault-app /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx

echo ""
echo "======================================"
echo " Server setup complete!"
echo " Next: Follow the deployment guide."
echo "======================================"
