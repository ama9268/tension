#!/bin/sh
set -e

# Ejecutar migraciones solo si se solicita explícitamente.
# La BD de producción ya tiene el esquema aplicado; solo activar
# cuando se despliegue un cambio de modelos:
#   RUN_MIGRATIONS=true docker compose up -d --build
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "==> [tension] Aplicando migraciones..."
    python manage.py migrate --noinput
else
    echo "==> [tension] Migraciones omitidas (RUN_MIGRATIONS != true)"
fi

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
