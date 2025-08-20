# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Копируем зависимости
COPY frontend/app/package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY frontend/app/ .

# Открываем порт для Vite
EXPOSE 5173

# Добавляем переменные окружения для Vite
ENV HOST=0.0.0.0
ENV PORT=5173

# Запускаем Vite в режиме разработки
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]