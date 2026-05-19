#!/usr/bin/env bash
# deploy.sh — первоначальный деплой на чистый Ubuntu 22.04
# Запускать от root: bash deploy.sh your-domain.com
# После первого запуска для обновлений используй: bash deploy.sh --update

set -euo pipefail

DOMAIN="${1:-}"
PROJECT_DIR="/opt/ai-shoper"
FRONTEND_DIST="/var/www/ai-shoper"

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
info()  { echo -e "\033[32m[OK]\033[0m $*"; }
warn()  { echo -e "\033[33m[!]\033[0m $*"; }
err()   { echo -e "\033[31m[ERR]\033[0m $*" >&2; exit 1; }

# ──────────────────────────────────────────────
# Режим обновления
# ──────────────────────────────────────────────
if [[ "${DOMAIN:-}" == "--update" ]]; then
    info "=== Обновление приложения ==="
    cd "$PROJECT_DIR"

    git pull origin main

    info "Пересборка backend..."
    docker compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache backend celery_worker celery_beat

    info "Сборка frontend..."
    cd frontend
    npm ci --prefer-offline
    npm run build
    cd ..
    rsync -a --delete frontend/dist/ "$FRONTEND_DIST/"

    info "Рестарт сервисов..."
    docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --remove-orphans

    nginx -t && systemctl reload nginx
    info "=== Готово ==="
    exit 0
fi

# ──────────────────────────────────────────────
# Первоначальный деплой
# ──────────────────────────────────────────────
[[ -z "$DOMAIN" ]] && err "Укажи домен: bash deploy.sh your-domain.com"
[[ $(id -u) -ne 0 ]] && err "Запускай от root"

info "=== Установка зависимостей ==="
apt-get update -qq
apt-get install -y -qq git curl nginx certbot python3-certbot-nginx nodejs npm

# Docker
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
fi

# Docker Compose plugin
if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi

info "=== Клонирование репозитория ==="
if [[ -d "$PROJECT_DIR/.git" ]]; then
    warn "Репозиторий уже есть, пропускаю клонирование"
else
    # Замени URL на свой репозиторий
    git clone https://github.com/YOUR_USERNAME/ai-shoper.git "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

info "=== Настройка .env.prod ==="
if [[ ! -f .env.prod ]]; then
    cp .env.example .env.prod
    warn "Заполни /opt/ai-shoper/.env.prod и запусти скрипт снова"
    warn "  nano /opt/ai-shoper/.env.prod"
    exit 0
fi

info "=== Сборка frontend ==="
cd frontend
npm ci
npm run build
cd ..
mkdir -p "$FRONTEND_DIST"
rsync -a --delete frontend/dist/ "$FRONTEND_DIST/"

info "=== Настройка nginx (HTTP) ==="
# Временный HTTP-только конфиг для certbot
cat > /etc/nginx/sites-available/ai-shoper <<NGINX_CONF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    root $FRONTEND_DIST;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { try_files \$uri \$uri/ /index.html; }
}
NGINX_CONF

ln -sf /etc/nginx/sites-available/ai-shoper /etc/nginx/sites-enabled/ai-shoper
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

info "=== Получение SSL-сертификата ==="
mkdir -p /var/www/certbot
certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos --email "$(grep OWNER_EMAIL .env.prod | cut -d= -f2 || echo admin@$DOMAIN)"

info "=== Установка продакшен nginx (HTTPS) ==="
sed "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf > /etc/nginx/sites-available/ai-shoper
nginx -t && systemctl reload nginx

info "=== Запуск Docker Compose ==="
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

info "=== Регистрация обновления certbot (cron) ==="
(crontab -l 2>/dev/null; echo "0 3 * * 1 certbot renew --quiet && systemctl reload nginx") | crontab -

info "=== Настройка Telegram webhook ==="
SECRET_KEY=$(grep SECRET_KEY .env.prod | cut -d= -f2)
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env.prod | cut -d= -f2)

if [[ -n "$SECRET_KEY" && -n "$BOT_TOKEN" ]]; then
    sleep 5  # дать backend время стартовать
    curl -s -X POST "https://$DOMAIN/api/v1/admin/setup-webhook" \
        -H "Content-Type: application/json" \
        -H "X-Admin-Secret: $SECRET_KEY" \
        -d "{\"url\": \"https://$DOMAIN/api/v1/telegram/webhook\"}" \
        | python3 -m json.tool
    info "Webhook зарегистрирован"
else
    warn "Заполни SECRET_KEY и TELEGRAM_BOT_TOKEN в .env.prod, затем выполни:"
    warn "  curl -X POST https://$DOMAIN/api/v1/admin/setup-webhook \\"
    warn "    -H 'X-Admin-Secret: YOUR_SECRET_KEY' \\"
    warn "    -H 'Content-Type: application/json' \\"
    warn "    -d '{\"url\": \"https://$DOMAIN/api/v1/telegram/webhook\"}'"
fi

info ""
info "======================================"
info " Деплой завершён!"
info "======================================"
info " Сайт:    https://$DOMAIN"
info " API:     https://$DOMAIN/api/v1/health"
info " Обновление: bash deploy.sh --update"
info "======================================"
