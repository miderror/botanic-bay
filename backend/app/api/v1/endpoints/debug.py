# backend/app/api/v1/endpoints/debug.py
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logger import logger

router = APIRouter()


class WebAppContext(BaseModel):
    """Контекст лога из WebApp"""

    url: str
    userAgent: str
    timestamp: str
    isTelegramWebApp: bool


class WebAppLog(BaseModel):
    """Модель лога из WebApp"""

    type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    context: Optional[WebAppContext] = None


@router.post("/webapp-logs")
async def receive_webapp_logs(log: WebAppLog):
    """
    Получение логов от Telegram WebApp

    Args:
        log: Данные лога из WebApp
    """
    prefix = f"[WebApp]"
    if log.user_id:
        prefix += f"[User:{log.user_id}]"

    # Формируем сообщение для лога
    message = f"{prefix} {log.message}"
    extra = {"context": log.context.dict() if log.context else None, "data": log.data}

    if log.type == "error":
        logger.error(message, extra=extra)
    elif log.type == "warn":
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)

    return {"status": "ok"}
