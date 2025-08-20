# docker/nginx/Dockerfile
FROM nginx:alpine

# Устанавливаем netcat для проверки доступности сервисов
RUN apk add --no-cache netcat-openbsd

# Удаляем дефолтный конфиг
RUN rm /etc/nginx/conf.d/default.conf

# НЕ копируем конфиг здесь, так как он будет монтироваться через volumes

# Копируем entrypoint скрипт
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Создаем директории для SSL и логов
RUN mkdir -p /etc/nginx/ssl /var/log/nginx

ENTRYPOINT ["/docker-entrypoint.sh"]