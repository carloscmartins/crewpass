#!/usr/bin/env bash
# CrewPass — bootstrap de deploy na VPS (passo único).
set -euo pipefail

DOMAIN_DEFAULT="crewpass.nordicusbot.com.br"

bold() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }

bold "CrewPass — bootstrap de deploy na VPS"
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

command -v docker >/dev/null || die "Docker não encontrado. Instale antes: https://docs.docker.com/engine/install/ubuntu/"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 não encontrado."
ok "Docker e Compose disponíveis"

read -r -p "Domínio do CrewPass [${DOMAIN_DEFAULT}]: " CP_DOMAIN
CP_DOMAIN=${CP_DOMAIN:-$DOMAIN_DEFAULT}

resolved=$(getent hosts "$CP_DOMAIN" | awk '{print $1; exit}' || true)
[ -n "$resolved" ] || die "DNS de '$CP_DOMAIN' não resolve."
ok "DNS de $CP_DOMAIN -> $resolved"

FRESH_ENV=0
if [ -f .env ]; then
    ok ".env já existe — mantendo"
else
    FRESH_ENV=1
    read -r -s -p "Senha do superusuário (Enter gera uma forte): " ADMIN_PASSWORD; echo
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-$(openssl rand -base64 18 | tr -d '/+=')}
    read -r -p "E-mail do admin [admin@${CP_DOMAIN}]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@$CP_DOMAIN}
    {
        echo "DJANGO_SECRET_KEY=$(openssl rand -hex 48)"
        echo "DJANGO_DEBUG=false"
        echo "DJANGO_ALLOWED_HOSTS=${CP_DOMAIN}"
        echo "DJANGO_CSRF_TRUSTED_ORIGINS=https://${CP_DOMAIN}"
        echo "DJANGO_SUPERUSER_EMAIL=${ADMIN_EMAIL}"
        echo "DJANGO_SUPERUSER_PASSWORD=${ADMIN_PASSWORD}"
    } > .env
    chmod 600 .env
    ok ".env criado"
fi

bold "Build e startup"
docker compose up -d --build

bold "Migrações"
docker compose exec -T web python manage.py migrate --noinput

bold "DEPLOY CONCLUÍDO"
ok "http://${CP_DOMAIN}  (admin via .env)"