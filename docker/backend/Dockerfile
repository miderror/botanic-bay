FROM python:3.11-slim AS python-base

# Создаем пользователя для приложения с домашней директорией
RUN addgroup --system app && \
    adduser --system --home /home/app --disabled-password --ingroup app app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    VENV_PATH="/opt/venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Устанавливаем Poetry и создаем виртуальное окружение в /opt/venv
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && python -m venv $VENV_PATH

# Копируем файлы зависимостей
WORKDIR /backend
COPY backend/pyproject.toml backend/poetry.lock ./

# Устанавливаем зависимости в /opt/venv
RUN poetry config virtualenvs.create false \
    && . $VENV_PATH/bin/activate \
    && poetry install --no-root --no-interaction

COPY docker/backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR /backend

# Создаем все необходимые директории и устанавливаем права
RUN mkdir -p /backend/media/products && \
    mkdir -p /backend/static && \
    mkdir -p /backend/logs && \
    touch /backend/logs/app.log && \
    chown -R app:app /backend/media && \
    chown -R app:app /backend/static && \
    chown -R app:app /backend/logs && \
    chmod -R 755 /backend/media && \
    chmod -R 755 /backend/static && \
    chmod -R 775 /backend/logs && \
    chmod 664 /backend/logs/app.log

RUN chown -R app:app /backend

# Установка необходимых утилит для сетевой диагностики
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       iputils-ping \
       dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Обновление корневых сертификатов
RUN update-ca-certificates

USER app

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]