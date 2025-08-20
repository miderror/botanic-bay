# backend/app/api/v1/endpoints/proxy.py
import httpx
from fastapi import APIRouter, HTTPException, Response

from app.core.logger import logger

router = APIRouter()


@router.get("/test")
async def test_proxy_route():
    """Тестовый маршрут для проверки доступности прокси"""
    return {"status": "ok", "message": "Proxy route is working"}


# Заменить на этот маршрут
@router.get("/widget/checkout-widget.js")
async def proxy_yookassa_widget_main():
    """
    Проксирует основной скрипт виджета ЮKассы через наш сервер
    """

    logger.info("Proxying YooKassa main script")
    return await proxy_yookassa_file("checkout-widget/v1/checkout-widget.js")


# Общий маршрут для остальных файлов
@router.get("/widget/{file_path:path}")
async def proxy_yookassa_widget(file_path: str):
    """
    Проксирует файлы виджета ЮKассы через наш сервер
    """
    return await proxy_yookassa_file(f"checkout-widget/v1/{file_path}")


async def proxy_yookassa_file(file_path: str):
    """
    Общая функция для проксирования файлов с домена ЮKассы

    Args:
        file_path: Путь к файлу на сервере ЮKассы

    Returns:
        Response с контентом файла
    """
    # Базовый URL ЮKассы
    base_url = "https://yookassa.ru"

    # Полный URL к запрашиваемому файлу
    full_url = f"{base_url}/{file_path}"

    logger.info(
        "Proxying YooKassa file", extra={"file_path": file_path, "full_url": full_url}
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, timeout=10.0)

            if response.status_code != 200:
                logger.error(
                    "Failed to proxy YooKassa file",
                    extra={
                        "url": full_url,
                        "status_code": response.status_code,
                    },
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch file from YooKassa",
                )

            # Определяем Content-Type на основе расширения файла
            content_type = "application/javascript"
            if file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".html"):
                content_type = "text/html"
            elif file_path.endswith(".json"):
                content_type = "application/json"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_path.endswith(".svg"):
                content_type = "image/svg+xml"

            logger.info(
                "Successfully proxied YooKassa file",
                extra={
                    "file_path": file_path,
                    "content_type": content_type,
                    "content_length": len(response.content),
                },
            )

            # Возвращаем ответ с правильным Content-Type
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",  # Кешируем на час
                    "X-Content-Type-Options": "nosniff",
                },
            )
    except Exception as e:
        logger.error(
            "Error proxying YooKassa file",
            extra={"url": full_url, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to proxy YooKassa file")
