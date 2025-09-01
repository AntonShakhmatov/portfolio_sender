#!/usr/bin/env sh
set -e

# Опционально: пропуск миграций
if [ "${SKIP_MIGRATIONS:-0}" = "1" ]; then
  echo "SKIP_MIGRATIONS=1 — пропускаю миграции"
  exec "$@"
fi

# Ждём БД (простая проверка TCP-порта)
if [ -n "${DB_HOST:-}" ]; then
  DB_PORT="${DB_PORT:-3306}"
  echo "Waiting for DB ${DB_HOST}:${DB_PORT}..."
  # busybox-alpine: используем nc
  until nc -z "${DB_HOST}" "${DB_PORT}" 2>/dev/null; do
    sleep 1
  done
  echo "DB is up."
fi

# Применяем миграции (idempotent)
php bin/console.php migrations:migrate --no-interaction --allow-no-migration

# Дальше — основной процесс контейнера (php-fpm/nginx/worker)
exec "$@"
