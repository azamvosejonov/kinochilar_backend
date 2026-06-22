#!/bin/bash
set -e

#######################################################
#  Kinochilar — Production Server Deployment (Docker'siz)
#  Ishlatish:  sudo bash deploy.sh
#######################################################

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

APP_DIR="/opt/kinochilar"
APP_USER="kinochilar"
DOMAIN="${DOMAIN:-kinochilar.uz}"

echo "========================================="
echo "  Kinochilar Production Deployment"
echo "========================================="
echo ""

# ── 1. System packages ────────────────────────────
log "Tizim paketlari o'rnatilmoqda..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip \
    postgresql postgresql-contrib nginx curl git \
    build-essential libpq-dev 2>/dev/null

# ── 2. Create app user ────────────────────────────
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
    log "Foydalanuvchi yaratildi: $APP_USER"
fi

# ── 3. Deploy application code ────────────────────
log "Kod serverga ko'chirilmoqda..."
mkdir -p "$APP_DIR"
cp -r /home/azam/Desktop/yaratish/kinochilar/app "$APP_DIR/"
cp /home/azam/Desktop/yaratish/kinochilar/requirements.txt "$APP_DIR/"
cp /home/azam/Desktop/yaratish/kinochilar/.env "$APP_DIR/"

# Copy bot if exists
if [ -d /home/azam/Desktop/kinochilar_bot ]; then
    cp -r /home/azam/Desktop/kinochilar_bot "$APP_DIR/bot"
    log "Telegram bot kodi ko'chirildi"
fi

# ── 4. Python virtual environment ─────────────────
log "Python muhiti sozlanmoqda..."
python3 -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$APP_DIR/requirements.txt" -q
pip install gunicorn -q
deactivate

# ── 5. Upload directories ─────────────────────────
log "Upload kataloglari yaratilmoqda..."
mkdir -p "$APP_DIR/uploads"/{videos,posters,backdrops}

# ── 6. PostgreSQL database ────────────────────────
log "PostgreSQL sozlanmoqda..."
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='kinochilar'" 2>/dev/null)
if [ "$DB_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE DATABASE kinochilar;" -q 2>/dev/null
    sudo -u postgres psql -c "CREATE USER kinochilar WITH PASSWORD 'kinochilar_db_pass_2024';" -q 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kinochilar TO kinochilar;" -q 2>/dev/null
    sudo -u postgres psql -d kinochilar -c "GRANT ALL ON SCHEMA public TO kinochilar;" -q 2>/dev/null
    log "Database yaratildi: kinochilar"
else
    warn "Database allaqachon mavjud: kinochilar"
fi

# Update .env for PostgreSQL
sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://kinochilar:kinochilar_db_pass_2024@localhost/kinochilar|' "$APP_DIR/.env"

# ── 7. Seed data ──────────────────────────────────
log "Seed ma'lumotlar yuklanmoqda..."
cd "$APP_DIR"
source venv/bin/activate
python3 seed.py 2>/dev/null || warn "seed.py ishlamadi (balki jadvallar allaqachon mavjud)"
python3 dummy_data.py 2>/dev/null || warn "dummy_data.py ishlamadi"
deactivate

# ── 8. Permissions ────────────────────────────────
log "Ruxsatlar sozlanmoqda..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── 9. systemd services ───────────────────────────
log "systemd servislar sozlanmoqda..."

cat > /etc/systemd/system/kinochilar-api.service << 'SERVICE'
[Unit]
Description=Kinochilar API Backend
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=kinochilar
Group=kinochilar
WorkingDirectory=/opt/kinochilar
Environment=PATH=/opt/kinochilar/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/opt/kinochilar/.env
ExecStart=/opt/kinochilar/venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 127.0.0.1:8080 \
    --access-logfile /var/log/kinochilar/access.log \
    --error-logfile /var/log/kinochilar/error.log \
    --capture-output
Restart=always
RestartSec=5
StandardOutput=append:/var/log/kinochilar/app.log
StandardError=append:/var/log/kinochilar/app.log

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/kinochilar-bot.service << 'SERVICE'
[Unit]
Description=Kinochilar Telegram Bot
After=network.target kinochilar-api.service
Wants=kinochilar-api.service

[Service]
Type=simple
User=kinochilar
Group=kinochilar
WorkingDirectory=/opt/kinochilar/bot
Environment=PATH=/opt/kinochilar/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/kinochilar/bot
Environment=BOT_TOKEN=7449553755:AAH6-xY-8XmS0z6e2iE1Uj-h9fXGf9q7Ivk
Environment=API_BASE_URL=http://127.0.0.1:8080/api/v1
ExecStart=/opt/kinochilar/venv/bin/python /opt/kinochilar/bot/run.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/kinochilar/bot.log
StandardError=append:/var/log/kinochilar/bot.log

[Install]
WantedBy=multi-user.target
SERVICE

mkdir -p /var/log/kinochilar
chown "$APP_USER:$APP_USER" /var/log/kinochilar

systemctl daemon-reload
log "systemd servislar yaratildi"

# ── 10. Nginx ─────────────────────────────────────
log "Nginx sozlanmoqda..."
cat > /etc/nginx/sites-available/kinochilar << 'NGINX'
server {
    listen 80;
    server_name _;

    client_max_body_size 500M;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_buffering off;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Video streaming
    location /stream/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Range $http_range;
        proxy_set_header If-Range $http_if_range;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # Static uploads
    location /uploads/ {
        alias /opt/kinochilar/uploads/;
        add_header Access-Control-Allow-Origin *;
        add_header Accept-Ranges bytes;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/kinochilar /etc/nginx/sites-enabled/kinochilar
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
log "Nginx sozlandi"

# ── 11. Start services ────────────────────────────
log "Servislar ishga tushirilmoqda..."
systemctl enable kinochilar-api
systemctl start kinochilar-api
systemctl enable kinochilar-bot 2>/dev/null || true
systemctl start kinochilar-bot 2>/dev/null || true

# ── 12. Firewall ──────────────────────────────────
if command -v ufw &>/dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    log "Firewall sozlandi (80, 443)"
fi

# ── Done ──────────────────────────────────────────
echo ""
echo "========================================="
echo "  Deploy yakunlandi!"
echo "========================================="
echo ""
echo "Backend API:    http://$DOMAIN/api/v1/"
echo "API Docs:       http://$DOMAIN/api/v1/docs"
echo "Health check:   curl http://127.0.0.1:8080/"
echo ""
echo "Buyruqlar:"
echo "  systemctl status kinochilar-api    # API holati"
echo "  systemctl status kinochilar-bot    # Bot holati"
echo "  systemctl restart kinochilar-api   # API ni qayta yuklash"
echo "  journalctl -u kinochilar-api -f    # Loglarni kuzatish"
echo "  tail -f /var/log/kinochilar/app.log # App log"
echo ""
echo "HTTPS uchun (ixtiyoriy):"
echo "  sudo apt install certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d $DOMAIN"
