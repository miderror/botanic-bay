import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logfire
import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import State
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.admin import init_admin
from app.api.middleware import log_request_middleware
from app.api.tags import Tags
from app.api.v1.router import api_router
from app.core.db import engine
from app.core.logger import logger
from app.core.settings import settings
from app.services.cdek.client import get_cdek_async_client
from app.services.scheduler import scheduler


class DebugTracebackMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled exception during request: {request.method} {request.url.path}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal Server Error", "error": str(e)},
            )


if settings.SENTRY_DSN:
    # Инициализация Sentry/Bugsink для отслеживания ошибок
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        send_default_pii=True,
        max_request_body_size="always",
        traces_sample_rate=0,
    )


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncGenerator[None, None]:
    """
    Контекстный менеджер для управления жизненным циклом приложения
    Выполняет инициализацию при запуске и освобождение ресурсов при завершении
    """
    # Код, выполняемый при запуске приложения (аналог startup)
    logger.info("Starting application...")
    app_instance.state = State()

    # Инициализация ЮКассы
    try:
        # Настраиваем SDK ЮКассы с данными из настроек
        from yookassa import Configuration

        Configuration.configure(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)
        logger.info("YooKassa SDK initialized successfully")

        # Удаляем автоматическую настройку вебхуков, так как они настроены вручную
        # через интерфейс ЮКассы

    except Exception as e:
        # Логируем ошибку, но позволяем приложению запуститься
        logger.error(
            "Failed to initialize YooKassa", extra={"error": str(e)}, exc_info=True
        )

    app_instance.state.cdek_client = get_cdek_async_client()
    logger.info("CDEK client initialized")

    logger.info(f"Application started in {settings.ENVIRONMENT} mode")

    # Запуск планировщика задач
    scheduler.start()

    # Передаем управление FastAPI для обработки запросов
    yield

    # Код, выполняемый при завершении работы приложения (аналог shutdown)
    logger.info("Shutting down application...")

    await app_instance.state.cdek_client.aclose()

    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TG Store API",
    openapi_tags=Tags.get_all_tags(),
    lifespan=lifespan,  # Используем наш контекстный менеджер для событий жизненного цикла
)

logfire.configure(
    send_to_logfire="if-token-present",
    token=settings.LOGFIRE_TOKEN or None,
    service_name=settings.LOGFIRE_SERVICE_NAME,
    console=False,
)
logfire.instrument_fastapi(
    app=app,
    capture_headers=True,
)

if settings.DEBUG:
    app.add_middleware(DebugTracebackMiddleware)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Добавляем middleware для логирования
app.middleware("http")(log_request_middleware)

init_admin(app, engine)

app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_DIR), name="media")
app.mount("/backend/media", StaticFiles(directory=settings.MEDIA_DIR), name="backend-media-hack")

# Подключаем API роутер
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Обработчики исключений
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Обработчик ошибок валидации запросов
    """
    error_details = str(exc.errors())
    logger.error(f"Request validation error: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Обработчик HTTP ошибок
    """
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Обработчик всех остальных ошибок
    """
    error_msg = str(exc)
    stack_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {error_msg}\n{stack_trace}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {error_msg}"},
    )


@app.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    """Проверка работоспособности API"""
    return {"status": "ok"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Проверка работоспособности API"""
    return {"status": "healthy"}
