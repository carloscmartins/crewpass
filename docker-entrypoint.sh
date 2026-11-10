#!/bin/sh
set -e

# Aplicar migrações
python manage.py migrate --noinput

# Criar superusuário se não existir (opcional, via variável de ambiente)
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput 2>/dev/null || true
fi

exec "$@"