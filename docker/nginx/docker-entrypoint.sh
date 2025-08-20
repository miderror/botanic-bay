#!/bin/sh
set -e

# Ждем доступности backend
until nc -z backend 8000; do
    echo "Waiting for backend..."
    sleep 1
done

# Проверяем конфигурацию Nginx перед запуском
echo "Checking Nginx configuration..."
nginx -t

# Если проверка прошла успешно, запускаем Nginx
if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Starting Nginx..."
    # Запускаем nginx
    nginx -g 'daemon off;'
else
    echo "ERROR: Nginx configuration is invalid. Please fix the configuration and restart the container."
    exit 1
fi