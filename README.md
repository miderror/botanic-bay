# Botanic Bay

Телеграм-магазин с веб-интерфейсом для продажи товаров через Telegram WebApp.

## Ссылки

- [Репо на GitHub](https://github.com/hazadus/bottec-botanic-bay)
- [Макет](https://www.figma.com/design/d8OdjVaVKNzsMhrinbxtQM/Botanic-Bay)
- [Логи Logfire](https://logfire-us.pydantic.dev/hazadus/botanic)
- [Bugsink Issues](http://85.193.91.88:8000/issues/3/)
- [Umami Tracker](https://stats.hazadus.ru/websites/60b7d664-a2d0-427b-8bfb-7045a5d4110d)

## Документация

- [Команды Makefile](docs/makefile.md)
- Бэкенд
   - [Архитектура](docs/backend/backend_architecture.md)
   - [Обработка ошибок](docs/backend/error_handling.md)

## Основные возможности

- Каталог товаров с фильтрацией и поиском
- Корзина и оформление заказов
- Интеграция с платёжной системой ЮKassa
- Интеграция с системой доставки СДЭК
- Интеграция со складским API
- Реферальная система
- Система бонусов и скидок
- Административная панель управления

## Технологии

- Backend: FastAPI, PostgreSQL, Redis, Celery
- Frontend: Vue.js, Telegram WebApp API
- Инфраструктура: Docker, Docker Compose

## Установка и запуск

### Требования

- Docker и Docker Compose
- Make (опционально, для удобства использования команд)

### Локальная разработка

1. Клонировать репозиторий:
```bash
git clone https://github.com/hazadus/bottec-botanic-bay
cd tg-store
```

2. Создать файлы .env в корневой директориях `backend` и `frontend` проекта (использовать соответствующие `.env.example` как шаблоны):

3. Настроить переменные окружения в файлах `backend/.env` и `frontend/.env`:
   - API ключ для Яндекс Карт получить в [кабинете разработчика](https://developer.tech.yandex.ru) - JavaScript API и HTTP Геокодер

4. Запустить проект:
```bash
# Используя Make
make build  # Собрать все контейнеры
make up     # Запустить проект
make migrate-up  # Применить миграции базы данных

# Или используя Docker Compose напрямую
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

5. Для загрузки товаров в базу данных, выполнить SQL из файла `scripts/seed_products.sql`

### Полезные команды

```bash
# Просмотр логов
make logs  # Все логи
make logs-backend  # Только логи бэкенда

# Работа с базой данных
make migrate-create name="Migration name"  # Создать новую миграцию
make migrate-up     # Применить все миграции
make migrate-down   # Откатить все миграции
make migrate-status # Показать статус миграций

# Доступ к консоли PostgreSQL
make psql

# Очистка и перезапуск
make clean  # Очистить все контейнеры и volumes
make reset  # Полностью пересоздать окружение

# Работа с дампами БД
make db-backup  # Создать дамп БД
make db-restore file=backup/filename.sql  # Восстановить БД из дампа
make db-list-backups  # Показать список доступных дампов
```

### Доступ к приложению

После запуска проект будет доступен по следующим адресам:

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

### Тесты бэкенда

1. Тесты запускаются в Докере при помощи команды `just test-backend`. При этом, каждый раз создаётся чистая база данных для интеграционных тестов и применяются миграции. Можно запустить тесты из отдельного файла командой вида `just test-backend tests/unit/event_dao_test.py`.
2. Файл настроек приложения для тестов `./backend/.env.test` редактировать не требуется.
3. Отчеты о покрытии кода тестами будут в `./backend/htmlcov/index.html`

### Тесты фронтенда

1. Выполнить `just test-frontend` или `just test-coverage-frontend`.
2. Отчеты о покрытии кода тестами будут в `./frontend/app/coverage/index.html`

## Разработка

### Структура проекта
```
tg-store/
├── backend/            # FastAPI backend
├── frontend/           # Vue.js frontend
├── docker/            # Docker конфигурации
├── docs/             # Документация
└── scripts/          # Вспомогательные скрипты
```

# Руководство по запуску проекта

## Быстрый старт

### Режим разработки
```bash
# Запуск проекта в режиме разработки
make dev

# Или пошагово:
make dev-build    # собрать контейнеры
make dev-up       # запустить контейнеры
make logs         # смотреть логи
```

### Режим продакшена
```bash
# Запуск проекта в продакшене
make prod

# Или пошагово:
make prod-build   # собрать контейнеры
make prod-up      # запустить контейнеры
make logs         # смотреть логи
```

## Основные различия между режимами

### Режим разработки
- Работает Vite dev server с Hot Module Replacement (HMR)
- Используется HTTP без SSL
- Монтируются локальные папки для быстрой разработки
- Включен режим отладки

### Режим продакшена
- Используется собранная production-версия фронтенда
- Настроен SSL через Let's Encrypt
- Оптимизированные настройки nginx
- Отключен режим отладки
- Минимальные права доступа для безопасности

### Дополнительные указания

Информация из Docker Compose - её ещё предстоит проверить:

> Важно создать папки и сделать права `777` для папов `backend/media`, `backend/static`, `backend/logs`
```bash
mkdir -p backend/media backend/static backend/logs
chmod 777 backend/media backend/static backend/logs
```

> ЭТО ВСЕ СОЗДАЕТСЯ АВТОМАТОМ ПРИ ЗАПУСКЕ make prod

> Сейчас файлы настроек хранятся в специальной папке env - именно оттуда они копируются в рабоую версию кода
```bash
	@cp ../env/env.backend backend/.env
	@cp ../env/env.frontend frontend/.env
```

> А также во `frontend/app/vite.config.ts` - использовать `vite.config.prod.ts`
> А также нужно скопировать `.env` файлы для `frontend` и `backend`
```bash
cp ../tg-store_0_2_2/backend/.env backend/.env
cp ../tg-store_0_2_2/frontend/.env frontend/.env
root@4209885-ez92999:/var/www/env# ls
env.backend  env.frontend
```

> Кроме того на стороне ЮКасса нам нужно установить правильный путь для отправки веб-хуков
> После загрузки новой версии нужно удалить все старое (имаджи и контенеры) и заново сделать билд
```bash
make prod-build
```
> Только потом уже запускать `make prod`

> Еще нужно скопировать media файлы
```bash
cp -r ../tg-store_0_2_2/backend/media/* backend/media/
```

### Что нужно сделать на сервере для работы GitHub Action:

1. **Создать SSH ключ для деплоя:**
   ```bash
   ssh-keygen -t ed25519 -C "deploy-key-bottec-botanic" -f ~/.ssh/deploy_key
   ```

2. **Добавить ключ в SSH конфиг:**
    ```bash
    cat >> ~/.ssh/config << EOF
    Host github.com
        HostName github.com
        User git
        IdentityFile ~/.ssh/deploy_key
    EOF
    ```

3. **Настроить git репозиторий:**
   ```bash
   cd /root/bottec-botanic-bay
   git remote set-url origin git@github.com:hazadus/bottec-botanic-bay.git
   ```

4. **Добавить публичный ключ в GitHub:**
   - Скопировать содержимое `cat ~/.ssh/deploy_key.pub`
   - В репозитории: Settings → Deploy keys → Add deploy key
   - Вставить ключ и сохранить

5. **Выполнить первый git pull вручную**
   - Ответить `yes` на вопрос:
   ```
   This key is not known by any other names
   Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
   ```
