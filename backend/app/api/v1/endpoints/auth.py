# backend/app/api/v1/endpoints/auth.py
import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_referral_service
from app.core.db import get_session
from app.core.logger import logger
from app.core.settings import settings
from app.schemas.user import SAuthResponse, SUserCreate
from app.services.referral.referral_service import ReferralService
from app.services.telegram.user_service import TelegramUserService

router = APIRouter()


class WebAppInitDataUnsafe(BaseModel):
    """Модель для небезопасных данных WebApp"""

    auth_date: str
    hash: str
    query_id: str
    user: dict


class WebAppValidationRequest(BaseModel):
    """Запрос на валидацию данных WebApp"""

    initData: str
    initDataUnsafe: Optional[WebAppInitDataUnsafe]


async def get_user_service(
    session: AsyncSession = Depends(get_session),
    referral_service: ReferralService = Depends(get_referral_service),
) -> TelegramUserService:
    return TelegramUserService(
        session,
        referral_service,
    )


def validate_telegram_hash(data_check_string: str, received_hash: str) -> bool:
    """
    Валидация хеша от Telegram WebApp

    Args:
        data_check_string: Строка для проверки
        received_hash: Полученный хеш для сравнения

    Returns:
        bool: True если хеш валиден
    """
    # Создаем секретный ключ из токена бота
    secret_key = hmac.new(
        b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    # Вычисляем хеш от data_check_string
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    logger.debug(
        "Hash comparison details",
        extra={
            "data_check_string": data_check_string,
            "calculated_hash": calculated_hash,
            "received_hash": received_hash,
        },
    )

    return calculated_hash == received_hash


@router.post("/validate-webapp")
async def validate_webapp_data(
    data: WebAppValidationRequest,
    user_service: TelegramUserService = Depends(get_user_service),
):
    """
    Валидирует данные от Telegram WebApp
    """
    try:
        logger.info("Starting WebApp data validation")

        # Проверяем наличие initData
        if not data.initData:
            raise ValueError("No init data provided")

        # Декодируем и разбираем параметры
        params = {}
        for key_value in data.initData.split("&"):
            key, value = key_value.split("=", 1)
            params[key] = unquote(value)

        # Извлекаем хеш
        received_hash = params.pop("hash", None)
        if not received_hash:
            raise ValueError("No hash in init data")

        # Сортируем оставшиеся параметры и создаем строку для проверки
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        logger.debug(
            "Validation parameters",
            extra={"params": params, "data_check_string": data_check_string},
        )

        # Проверяем валидность хеша
        if not validate_telegram_hash(data_check_string, received_hash):
            raise ValueError("Invalid hash")

        # Получаем данные пользователя
        user_data = json.loads(params["user"])

        logger.info(
            "WebApp data validated successfully",
            extra={"user_id": user_data["id"], "username": user_data.get("username")},
        )

        # После успешной валидации и получения user_data добавляем:
        user = await user_service.register_user(
            telegram_id=user_data["id"],
            username=user_data.get("username"),
            full_name=f"{user_data['first_name']} {user_data.get('last_name', '')}",
        )

        logger.info(
            "WebApp data validated successfully",
            extra={"user_id": user.telegram_id, "username": user.username},
        )

        return {
            "id": user_data["id"],
            "username": user_data.get("username"),
            "first_name": user_data["first_name"],
            "last_name": user_data.get("last_name", ""),
        }

    except Exception as e:
        logger.error("WebApp validation failed", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register", response_model=SAuthResponse)
async def register_user(
    user_data: SUserCreate,
    user_service: TelegramUserService = Depends(get_user_service),
) -> SAuthResponse:
    """
    Регистрация пользователя через Telegram WebApp

    Args:
        user_data: Данные пользователя
        user_service: Сервис для работы с пользователями

    Returns:
        SAuthResponse: Ответ с данными пользователя, включая роли
    """
    try:
        logger.info(f"Registering user with Telegram ID: {user_data.telegram_id}")
        user = await user_service.register_user(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            full_name=user_data.full_name,
            referral_code=user_data.referral_code,
        )

        # Преобразуем ответ, включая роли
        response_data = {
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "referral_code": user.referral_code,
                "is_active": user.is_active,
                "roles": user.role_names,  # Используем новый метод
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            "message": "Registration successful",
            "status": "success",
        }

        logger.info(
            "User successfully registered",
            extra={
                "telegram_id": user.telegram_id,
                "username": user.username,
                "roles": user.role_names,
            },
        )

        return SAuthResponse(**response_data)

    except Exception as e:
        logger.error("Registration failed", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
