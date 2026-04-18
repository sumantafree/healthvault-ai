# HealthVault AI — Linux Server Deployment Guide

## What You Need Before Starting

| Requirement | Details |
|-------------|---------|
| Linux server | Ubuntu 22.04 LTS (VPS or shared server with SSH) |
| SSH access | Root or sudo user |
| Domain name | e.g. `yourdomain.com` |
| DNS access | Ability to add A/CNAME records |
| Supabase project | Already set up (cloud DB + storage) |
| OpenAI/Gemini key | For AI features |

**Subdomains we will create:**
- `app.yourdomain.com` → Next.js frontend
- `api.yourdomain.com` → FastAPI backend

---

## STEP 1 — DNS Setup (Do this first, takes ~30 min to propagate)

Log in to your **domain registrar** (GoDaddy, Namecheap, Cloudflare, etc.)  
Go to DNS Management and add these **A records**:

| Type | Host/Name | Value | TTL |
|------|-----------|-------|-----|
| A | `app` | `YOUR_SERVER_IP` | 300 |
| A | `api` | `YOUR_SERVER_IP` | 300 |

**To find your server IP:**
```bash
curl ifconfig.me
```

**Verify DNS has propagated (run from your local machine):**
```bash
nslookup app.yourdomain.com
nslookup api.yourdomain.com
# Both should return your server IP
```

---

## STEP 2 — Connect to Your Server

```bash
ssh root@YOUR_SERVER_IP
# or if using a non-root user:
ssh youruser@YOUR_SERVER_IP
```

---

## STEP 3 — Upload Your Project Files

**Option A — Git (recommended):**
```bash
# On your server:
cd /var/www
git clone https://github.com/YOUR_USERNAME/healthvault-ai.git
# or use a private repo with a deploy key
```

**Option B — SCP from your Windows machine:**
```bash
# Run from Windows PowerShell / Git Bash:
scp -r G:/Ai-assitent/healthvault-ai root@YOUR_SERVER_IP:/var/www/healthvault-ai
```

**Option C — FTP/SFTP:**  
Use FileZilla or WinSCP to upload the entire `healthvault-ai` folder to `/var/www/healthvault-ai`

---

## STEP 4 — Run the Server Setup Script

```bash
# On the server (as root):
cd /var/www/healthvault-ai

# Edit the domain in the setup script first:
nano scripts/setup-server.sh
# Change: DOMAIN="yourdomain.com"  ← put your actual domain

# Make executable and run:
chmod +x scripts/setup-server.sh
sudo bash scripts/setup-server.sh
```

This installs: Nginx, Python 3.11, Node.js 20, Tesseract OCR, PM2, Certbot, UFW firewall.

---

## STEP 5 — Set Up the Python Virtual Environment

```bash
cd /var/www/healthvault-ai

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Verify gunicorn is installed
gunicorn --version

# Deactivate
deactivate
```

---

## STEP 6 — Configure Backend Environment Variables

```bash
cd /var/www/healthvault-ai/backend

# Copy the example env file
cp ../.env.example .env

# Edit it with your actual values
nano .env
```

Fill in every value in `.env`:

```env
APP_ENV=production
SECRET_KEY=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">

DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@db.PROJECTREF.supabase.co:5432/postgres
SUPABASE_URL=https://PROJECTREF.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

OPENAI_API_KEY=sk-...
AI_PROVIDER=openai

TWILIO_ACCOUNT_SID=AC...          # for WhatsApp (Sprint 5)
TWILIO_AUTH_TOKEN=...

ALLOWED_ORIGINS=https://app.yourdomain.com
TESSERACT_CMD=/usr/bin/tesseract
```

**Get Supabase credentials:**  
Go to [supabase.com](https://supabase.com) → Your Project → Settings → API

---

## STEP 7 — Run the Database Schema

```bash
# Option A — Supabase SQL editor (easiest):
# 1. Open https://supabase.com → Your project → SQL Editor
# 2. Copy the contents of:  db/schema.sql
# 3. Paste into SQL Editor and click Run

# Option B — psql from your server:
source venv/bin/activate
psql "postgresql://postgres:PASSWORD@db.PROJECTREF.supabase.co:5432/postgres" \
     -f /var/www/healthvault-ai/db/schema.sql
```

---

## STEP 8 — Install the Backend as a Systemd Service

```bash
# Copy service file
sudo cp /var/www/healthvault-ai/scripts/healthvault-api.service \
        /etc/systemd/system/healthvault-api.service

# Set correct permissions on app directory
sudo chown -R www-data:www-data /var/www/healthvault-ai
sudo chmod -R 755 /var/www/healthvault-ai

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable healthvault-api
sudo systemctl start healthvault-api

# Check it is running:
sudo systemctl status healthvault-api
```

Expected output: `Active: active (running)`

**Test the backend:**
```bash
curl http://127.0.0.1:8000/health
# Should return: {"status":"healthy","app":"HealthVault AI",...}
```

---

## STEP 9 — Build and Start the Frontend

```bash
cd /var/www/healthvault-ai/frontend

# Install Node dependencies
npm install

# Edit ecosystem config with your real values
nano ecosystem.config.js
# Set: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY,
#      NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Build the Next.js app:**
```bash
# Set env for build
export NEXT_PUBLIC_SUPABASE_URL=https://PROJECTREF.supabase.co
export NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
export NEXT_PUBLIC_API_URL=https://api.yourdomain.com

npm run build
# This takes 1-3 minutes. Should end with "Route (app)" table
```

**Start with PM2:**
```bash
pm2 start ecosystem.config.js

# Save PM2 process list (survives server reboot)
pm2 save

# Configure PM2 to start on system boot:
pm2 startup
# It will print a command like:
#   sudo env PATH=... pm2 startup systemd -u root --hp /root
# COPY and RUN that exact command
```

**Check it is running:**
```bash
pm2 status
# Should show: healthvault-app | online
```

```bash
curl http://127.0.0.1:3000
# Should return HTML
```

---

## STEP 10 — Enable Nginx (HTTP first, test before SSL)

Edit both nginx configs to temporarily serve HTTP only for testing:

```bash
# Replace domain placeholder in nginx configs:
sudo sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN.com/g' \
    /etc/nginx/sites-available/healthvault-api \
    /etc/nginx/sites-available/healthvault-app
```

**Temporarily set up HTTP-only to test (remove SSL lines):**
```bash
sudo nano /etc/nginx/sites-available/healthvault-api
```

Replace the entire file contents with this temporary HTTP version:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 25M;
        proxy_read_timeout 300s;
    }
}
```

Do the same for the frontend:
```bash
sudo nano /etc/nginx/sites-available/healthvault-app
```
```nginx
server {
    listen 80;
    server_name app.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Test nginx config and reload
sudo nginx -t
sudo systemctl reload nginx
```

**Test HTTP access:**
```bash
curl http://api.yourdomain.com/health
# Expected: {"status":"healthy",...}

curl -I http://app.yourdomain.com
# Expected: HTTP/1.1 200 OK
```

---

## STEP 11 — Install SSL Certificates (HTTPS)

```bash
# Install certs for both subdomains:
sudo certbot --nginx -d api.yourdomain.com
sudo certbot --nginx -d app.yourdomain.com

# Follow prompts:
# - Enter your email address
# - Agree to terms (A)
# - Choose redirect HTTP to HTTPS (2)
```

Certbot **automatically edits** your nginx configs to add SSL.

**Now copy in the production nginx configs:**
```bash
sudo cp /var/www/healthvault-ai/nginx/api.conf \
        /etc/nginx/sites-available/healthvault-api

sudo cp /var/www/healthvault-ai/nginx/app.conf \
        /etc/nginx/sites-available/healthvault-app

# Replace domain placeholder
sudo sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN.com/g' \
    /etc/nginx/sites-available/healthvault-api \
    /etc/nginx/sites-available/healthvault-app

sudo nginx -t
sudo systemctl reload nginx
```

**Verify SSL:**
```bash
curl https://api.yourdomain.com/health
curl -I https://app.yourdomain.com
```

**Auto-renew certificates** (already set by certbot, verify):
```bash
sudo certbot renew --dry-run
# Should say: Congratulations, all simulated renewals succeeded
```

---

## STEP 12 — Configure Supabase OAuth Redirect URLs

**In Supabase Dashboard:**
1. Go to Authentication → URL Configuration
2. Set **Site URL** to: `https://app.yourdomain.com`
3. Add to **Redirect URLs**:
   - `https://app.yourdomain.com/auth/callback`

**In Google Cloud Console** (for Google OAuth):
1. Go to APIs & Services → Credentials → Your OAuth client
2. Add to **Authorized redirect URIs**:
   - `https://YOUR_SUPABASE_PROJECT.supabase.co/auth/v1/callback`

---

## STEP 13 — Final Verification Checklist

Run these checks after deployment:

```bash
# 1. Backend health check
curl https://api.yourdomain.com/health

# 2. Backend docs (should return 404 in production — docs are disabled)
curl https://api.yourdomain.com/docs

# 3. Frontend accessible
curl -I https://app.yourdomain.com

# 4. Services running
sudo systemctl status healthvault-api
pm2 status

# 5. View logs
sudo journalctl -u healthvault-api -f         # backend logs
pm2 logs healthvault-app                      # frontend logs
tail -f /var/log/healthvault/error.log        # gunicorn errors
```

**Open in browser:**
- `https://app.yourdomain.com` → should show HealthVault AI login page
- Click "Continue with Google" → should redirect to Google OAuth

---

## Deploying Updates (After First Setup)

Every time you make code changes and want to redeploy:

```bash
# On your server:
cd /var/www/healthvault-ai

# If using Git:
git pull origin main

# Or re-upload changed files via SCP/SFTP

# Then run the deploy script:
bash scripts/deploy.sh
```

---

## Useful Management Commands

```bash
# ── Backend ─────────────────────────────────────────────────────
sudo systemctl restart healthvault-api    # restart backend
sudo systemctl stop healthvault-api       # stop backend
sudo systemctl status healthvault-api     # check status
sudo journalctl -u healthvault-api -n 50  # last 50 log lines

# ── Frontend ────────────────────────────────────────────────────
pm2 restart healthvault-app               # restart frontend
pm2 stop healthvault-app                  # stop frontend
pm2 logs healthvault-app --lines 50       # last 50 log lines
pm2 monit                                 # live monitoring dashboard

# ── Nginx ───────────────────────────────────────────────────────
sudo nginx -t                             # test config
sudo systemctl reload nginx              # apply config changes
sudo systemctl restart nginx             # full restart

# ── SSL renewal ─────────────────────────────────────────────────
sudo certbot renew                        # renew certificates
```

---

## Troubleshooting

### "502 Bad Gateway" on api.yourdomain.com
```bash
# Check if backend is running:
sudo systemctl status healthvault-api
curl http://127.0.0.1:8000/health

# Check error logs:
sudo journalctl -u healthvault-api -n 30
tail -f /var/log/healthvault/error.log
```

### "Connection refused" on port 3000
```bash
pm2 status
pm2 restart healthvault-app
pm2 logs healthvault-app
```

### Frontend shows "Network Error" when calling API
```bash
# Check ALLOWED_ORIGINS in backend .env
nano /var/www/healthvault-ai/backend/.env
# Must include: ALLOWED_ORIGINS=https://app.yourdomain.com

sudo systemctl restart healthvault-api
```

### Google OAuth redirect fails
- Verify Supabase Site URL is set to `https://app.yourdomain.com`
- Verify redirect URL `https://app.yourdomain.com/auth/callback` is in Supabase allowed list
- Check browser console for CORS errors

### "Permission denied" errors
```bash
sudo chown -R www-data:www-data /var/www/healthvault-ai
sudo chmod -R 755 /var/www/healthvault-ai
```

### Out of memory during npm build
```bash
# Add swap space (1GB):
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
# Then retry npm run build
```

---

## Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 1 GB | 2 GB |
| CPU | 1 vCPU | 2 vCPU |
| Disk | 10 GB | 20 GB |
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |
