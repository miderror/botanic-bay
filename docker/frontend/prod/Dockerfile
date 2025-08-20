FROM node:20-alpine

WORKDIR /app

# Копируем зависимости
COPY frontend/app/package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY frontend/app/ .

# Копируем .env файл для доступа к переменным окружения во время сборки
COPY frontend/.env ../.env

# ВАЖНО: Заменить vite.config.ts на продакшен версию
COPY frontend/app/vite.config.prod.ts ./vite.config.ts

# Очистка и запуск сборки явно при сборке образа
RUN rm -rf /app/dist/* && npm run build

# Проверяем, чтобы удостовериться, что файлы есть
RUN ls -la /app/dist || true

# Запускаем бесконечную команду, чтобы контейнер не завершал работу
CMD ["tail", "-f", "/dev/null"]