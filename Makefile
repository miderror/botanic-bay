# Определение файла docker-compose (по умолчанию используем dev)
DC_FILE ?= docker-compose.dev.yml

# Определяем команду docker-compose с нужным файлом
DC := docker-compose -f $(DC_FILE)

.PHONY: build up down logs test migrate install

# ==========================================
# Команды для разработки
# ==========================================

dev-build: ## Собрать контейнеры для разработки
	docker-compose -f docker-compose.dev.yml build

dev-up: ## Запустить в режиме разработки
	docker-compose -f docker-compose.dev.yml up -d --remove-orphans

dev-down: ## Остановить контейнеры разработки
	docker-compose -f docker-compose.dev.yml down

dev: dev-down dev-up logs ## Запустить проект в режиме разработки с логами

dev-rb: ## Пересобрать и перезапустить сервисы (dev)
	docker-compose -f docker-compose.dev.yml up -d --no-deps --build backend frontend telegram_bot nginx

dev-rb-frontend: ## Пересобрать и перезапустить сервисы (dev)
	docker-compose -f docker-compose.dev.yml up -d --no-deps --build frontend

dev-rb-bot: ## Пересобрать и перезапустить telegram_bot (dev)
	docker-compose -f docker-compose.dev.yml up -d --no-deps --build telegram_bot

dev-rb-nginx: ## Пересобрать и перезапустить nginx (dev)
	docker-compose -f docker-compose.dev.yml up -d --no-deps --build nginx

dev-rs: ## Перезапустить сервисы (dev)
	docker-compose -f docker-compose.dev.yml restart backend frontend telegram_bot nginx

# ==========================================
# Команды для продакшена
# ==========================================

clean-frontend-dist: ## Удалить volume frontend_dist
	@echo "Удаление volume frontend_dist..."
	docker volume rm tg_store_frontend_dist || true
	@echo "Volume frontend_dist удален"

copy-env: ## Копировать .env файлы из ../env в соответствующие директории
	@echo "Копирование .env файлов..."
	@cp ../env/env.backend backend/.env
	@cp ../env/env.frontend frontend/.env
	@echo "Файлы .env успешно скопированы"
	
prod-prepare-dirs: ## Создать необходимые директории для продакшена и установить права
	@echo "Setting required permissions for backend directories..."
	mkdir -p backend/media backend/static backend/logs
	chmod -R 777 backend/media backend/static backend/logs
	@echo "Directory permissions set successfully"

prod-build: ## Собрать контейнеры для продакшена
	docker-compose -f docker-compose.prod.yml build

prod-build-no-cache: ## Собрать контейнеры для продакшена (без кэша)
	docker-compose -f docker-compose.prod.yml build --no-cache

prod-up: ## Запустить в режиме продакшена
	docker-compose -f docker-compose.prod.yml up -d --remove-orphans

prod-down: ## Остановить контейнеры продакшена
	docker-compose -f docker-compose.prod.yml down

prod: prod-prepare-dirs copy-env clean-frontend-dist prod-up migrate-up logs ## Запустить проект в продакшене с логами

prod-rb: ## Пересобрать и перезапустить сервисы (prod)
	docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend frontend telegram_bot nginx

prod-rb-bot: ## Пересобрать и перезапустить telegram_bot (prod)
	docker-compose -f docker-compose.prod.yml up -d --no-deps --build telegram_bot

prod-rb-nginx: ## Пересобрать и перезапустить nginx (prod)
	docker-compose -f docker-compose.prod.yml up -d --no-deps --build nginx

prod-rs: ## Перезапустить сервисы (prod)
	docker-compose -f docker-compose.prod.yml restart backend frontend telegram_bot nginx

prod-rebuild-frontend: clean-frontend-dist ## Пересобрать только frontend с очисткой volume
	docker-compose -f docker-compose.prod.yml up -d --no-deps --build frontend
	docker-compose -f docker-compose.prod.yml restart nginx	

# ==========================================
# Общие команды для логов
# ==========================================

logs: ## Показать логи всех контейнеров
	$(DC) logs -f --tail=100

logs-backend: ## Показать логи только backend
	$(DC) logs -f --tail=100 backend

logs-frontend: ## Показать логи только frontend
	$(DC) logs -f --tail=100 frontend

logs-bot: ## Показать логи только telegram_bot
	$(DC) logs -f --tail=100 telegram_bot

logs-nginx: ## Показать логи только nginx
	$(DC) logs -f --tail=100 nginx

# ==========================================
# Команды для работы с базой данных
# ==========================================

migrate-create: ## Создать новую миграцию (использование: make migrate-create name="Migration name")
	$(DC) exec backend alembic revision --autogenerate -m "$(name)"

migrate-up: ## Применить все миграции
	$(DC) exec backend alembic upgrade head

migrate-down: ## Откатить все миграции
	$(DC) exec backend alembic downgrade base

migrate-status: ## Показать статус миграций
	$(DC) exec backend alembic current

init-roles: ## Инициализация ролей (заполняем БД ролями)
	$(DC) exec backend python /backend/scripts/init_db.py

db-backup: ## Создание дампа БД
	@mkdir -p backup
	@echo "Creating database backup..."
	$(DC) exec postgres pg_dump -U postgres tg_store > backup/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed"

db-restore: ## Восстановление БД из файла (использование: make db-restore file=backup/filename.sql)
	@if [ -z "$(file)" ]; then \
		echo "Error: Please specify the backup file using 'file=backup/filename.sql'"; \
		exit 1; \
	fi
	@echo "Restoring database from $(file)..."
	$(DC) exec -T postgres psql -U postgres -d tg_store < $(file)
	@echo "Restore completed"

db-list-backups: ## Показать список доступных дампов
	@echo "Available database backups:"
	@ls -lh backup/*.sql 2>/dev/null || echo "No backups found"

# ==========================================
# Команды для разработки
# ==========================================

install: ## Установить зависимости локально
	cd backend && poetry install

format: ## Отформатировать код
	cd backend && poetry run black .
	cd backend && poetry run isort .

lint: ## Проверить код
		cd backend && poetry run flake8 .
	cd backend && poetry run mypy .

test: ## Запустить тесты
	$(DC) run --rm backend pytest -v

# ==========================================
# Утилиты
# ==========================================

nginx-config-check: ## Проверить конфигурацию Nginx внутри Docker-сети
	@echo "Проверка конфигурации Nginx внутри контейнера..."
	@docker-compose -f docker-compose.dev.yml exec nginx nginx -t || \
		(echo "Ошибка конфигурации! Детали выше." && exit 1)

nginx-fix-config: ## Создать временный Nginx контейнер для тестирования конфигурации
	@echo "Запуск временного Nginx для проверки конфигурации..."
	@docker-compose -f docker-compose.dev.yml stop nginx || true
	@docker run --rm \
		--network tg_store_network \
		-v $(PWD)/docker/nginx/conf.d/dev.conf:/etc/nginx/conf.d/default.conf:ro \
		nginx:alpine sh -c "echo 'Содержимое файла в контейнере:' && echo '------------------' && cat /etc/nginx/conf.d/default.conf && echo '------------------' && nginx -t" || \
		(echo "Ошибка конфигурации! Исправьте ошибки и повторите." && exit 1)
		
nginx-config-test:
	@echo "Проверка конфигурации Nginx..."
	@docker run --rm \
		--network tg_store_network \
		-v $(PWD)/docker/nginx/conf.d/dev.conf:/etc/nginx/conf.d/default.conf:ro \
		nginx:alpine nginx -t

nginx-reload:
	@echo "Перезагрузка конфигурации Nginx без перезапуска контейнера..."
	@docker-compose -f docker-compose.dev.yml exec nginx nginx -s reload

dev-nginx-reload: ## Проверить конфигурацию и перезагрузить Nginx
	@echo "Checking Nginx configuration..."
	@docker-compose -f docker-compose.dev.yml exec nginx nginx -t && \
	echo "Configuration OK, reloading Nginx..." && \
	docker-compose -f docker-compose.dev.yml exec nginx nginx -s reload || \
	echo "Configuration error, please fix and try again"

redis-flush: ## Очистить Redis
	$(DC) exec redis redis-cli FLUSHALL

redis-status: ## Показать статус Redis
	$(DC) exec redis redis-cli INFO | grep "connected"

psql: ## Открыть PostgreSQL консоль
	$(DC) exec postgres psql -U postgres -d tg_store

backend-shell: ## Открыть shell в контейнере backend
	$(DC) exec backend /bin/bash

	status: ## Показать статус контейнеров
	$(DC) ps

hard-stop: ## Полная остановка контейнеров
	docker stop $(docker ps -a -q)

clean: ## Очистить все контейнеры и volumes
	$(DC) down -v
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

purge: ## Полностью очистить Docker окружение
	$(DC) down -v
	docker rm -f redis || true
	docker container prune -f
	docker system prune -f

snapshot: ## Создание снапшота кода
	project-summary -v

# ==========================================
# Help команда
# ==========================================

help: ## Показать это сообщение
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
   	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Этот трюк позволяет передавать аргументы в цель
%:
	@: