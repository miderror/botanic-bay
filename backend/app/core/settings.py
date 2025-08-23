# backend/app/core/settings.py
import os
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определяем корневую директорию проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Загружаем переменные окружения
load_dotenv()


class Settings(BaseSettings):
    def __init__(self):
        super().__init__()
        self._update_time = datetime.now()

        # Создаем необходимые директории
        self.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Project info
    PROJECT_NAME: str = "TG Store API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Observability
    LOGFIRE_TOKEN: str | None = Field(default=None)
    LOGFIRE_SERVICE_NAME: str = Field(default="Backend")
    SENTRY_DSN: str | None = Field(default=None)

    # Environment settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Dev ngrok settings
    NGROK_URL: str

    # Frontend settings
    FRONTEND_URL: str = Field(default_factory=lambda: os.getenv("NGROK_URL"))

    # CORS settings
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:8080",
            os.getenv("NGROK_URL"),
        ]
    )

    # Upload settings
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Media settings
    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: Path = BASE_DIR / "media"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "tg_store"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_ECHO: bool = False

    @property
    def POSTGRES_URL(self) -> str:
        """Формирует URL для подключения к PostgreSQL"""
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        """Формирует URL для подключения к Redis"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery settings
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL

    # Directory settings
    STATIC_DIR: Path = BASE_DIR / "static"
    MEDIA_DIR: Path = BASE_DIR / "media"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # Payment Gateway settings (YooKassa)
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    YOOKASSA_WEBHOOK_URL_DEV: str
    YOOKASSA_WEBHOOK_URL_PROD: str

    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD_HASH: str

    # CDEK API settings
    CDEK_BASE_URL: str = "https://api.cdek.ru"
    CDEK_TEST_BASE_URL: str = "https://api.edu.cdek.ru"
    CDEK_CLIENT_ID: str
    CDEK_CLIENT_SECRET: SecretStr
    CDEK_TEST_MODE: bool = True
    CDEK_WEBHOOK_URL: str

    YANDEX_GEOCODER_API_KEY: SecretStr

    # Referral system settings
    REFERRAL_BONUS_AMOUNT: float = 100.0  # Бонус за приглашение (в рублях)
    REFERRAL_MINIMUM_WITHDRAWAL: float = 1000.0  # Минимальная сумма для вывода
    REFERRAL_MAX_LEVEL: int = 5
    REFERRAL_LEVELS: dict = {
        1: Decimal("0.08"),
        2: Decimal("0.05"),
        3: Decimal("0.04"),
        4: Decimal("0.02"),
        5: Decimal("0.01"),
    }

    # Discount system settings
    BRONZE_DISCOUNT_THRESHOLD: float = 10000.0  # Порог для бронзового уровня
    SILVER_DISCOUNT_THRESHOLD: float = 30000.0  # Порог для серебряного уровня
    GOLD_DISCOUNT_THRESHOLD: float = 50000.0  # Порог для золотого уровня

    BRONZE_DISCOUNT_PERCENT: float = 5.0  # Скидка для бронзового уровня
    SILVER_DISCOUNT_PERCENT: float = 7.0  # Скидка для серебряного уровня
    GOLD_DISCOUNT_PERCENT: float = 10.0  # Скидка для золотого уровня

    DISCOUNT_THRESHOLDS: list[tuple[float, float]] = [
        (GOLD_DISCOUNT_THRESHOLD, GOLD_DISCOUNT_PERCENT),
        (SILVER_DISCOUNT_THRESHOLD, SILVER_DISCOUNT_PERCENT),
        (BRONZE_DISCOUNT_THRESHOLD, BRONZE_DISCOUNT_PERCENT),
    ]

    # Order settings
    ORDER_ASSEMBLY_DEADLINE_HOUR: int = 15  # Час дня для дедлайна сборки заказа
    WAREHOUSE_UPDATE_INTERVAL: int = 120  # Интервал обновления остатков (в секундах)

    # Корзина
    CART_LIFETIME_MINUTES: int = 30  # Время жизни корзины в минутах

    # Cache settings
    CACHE_EXPIRE_IN_SECONDS: int = 300  # 5 минут

    # Logging settings
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"

    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Конфигурация для загрузки из файла .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    """Создает экземпляр настроек с кэшированием"""
    return Settings()


# Создаем глобальный экземпляр настроек
settings = get_settings()
