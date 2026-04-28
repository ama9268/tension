#!/bin/sh
set -e

echo "==> [tension] Aplicando migraciones..."
python manage.py migrate --noinput

echo "==> [tension] Recogiendo archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> [tension] Iniciando Gunicorn (workers=${GUNICORN_WORKERS:-3})..."
exec gunicorn \
    --workers "${GUNICORN_WORKERS:-3}" \
    --bind "0.0.0.0:8000" \
    --timeout 90 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    tension_project.wsgi:application
