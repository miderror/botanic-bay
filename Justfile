# Запустить проект в Докере в режиме разработки
dev:
    docker compose -f docker-compose.dev.yml up --remove-orphans

# Создать туннель для доступа к локальному серверу из Тelegram
tunnel:
    tuna http 80 --subdomain=botanic

# Применить все миграции
migrate-up:
    docker exec botanic-backend alembic upgrade head

# Форматировать код бэкенда с помощью black и isort
format-backend:
    @echo "🧹 Форматирование кода бэкенда..."
    cd backend && black app tests
    cd backend && isort app tests
    @echo "✅ Код бэкенда отформатирован"

# Проверить только изменённые в git .py файлы с помощью mypy
lint-backend:
    @echo "🔍 Проверка изменённых .py файлов mypy..."
    cd backend && files=$(git diff --name-only --diff-filter=ACMRTUXB HEAD | grep '\.py$' | sed 's|^backend/||') && [ -n "$files" ] && poetry run mypy $files || echo 'Нет изменённых .py файлов для проверки'
    @echo "✅ Проверка завершена"

# Проверит код фронтенда с помощью eslint
lint-frontend:
    @echo "🔍 Проверка кода фронтенда с помощью eslint..."
    cd frontend/app && npm run lint
    @echo "✅ Проверка кода фронтенда завершена"

# Посчитать строки кода в проекте и сохранить в файл
cloc:
    cloc --fullpath --exclude-list-file=.clocignore --md . > cloc.md

# Сгенерировать сообщение коммита (см. https://github.com/hazadus/gh-commitmsg)
commitmsg:
    gh commitmsg --language russian --examples

# Запустить тесты бэкенда в Докере
# Параметр test_path (опциональный): путь к конкретному тесту, например tests/unit/event_dao_test.py
test-backend test_path="":
    #!/bin/bash
    if [ -n "{{test_path}}" ]; then \
        docker compose -f docker-compose.test.yml run --rm -e PYTEST_PATH="{{test_path}}" app-test; \
    else \
        docker compose -f docker-compose.test.yml run --rm app-test; \
    fi || true
    docker compose -f docker-compose.test.yml down --volumes
    docker image rm bottec-botanic-bay-app-test

# Запустить тесты фронтенда
test-frontend:
    cd frontend/app && npm run test:run

# Запустить тесты фронтенда с покрытием
test-coverage-frontend:
    cd frontend/app && npm run test:coverage
